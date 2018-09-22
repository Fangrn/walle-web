#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: wushuiyong
# @Created Time : 日  1/ 1 23:43:12 2017
# @Description:

from flask_login import UserMixin
from sqlalchemy import String, Integer, Text, DateTime, or_
from werkzeug.security import check_password_hash, generate_password_hash

# from flask_cache import Cache
from datetime import datetime
from walle.service.extensions import login_manager
from walle.model.database import SurrogatePK, db, relationship, Model
from walle.model.tag import TagModel
from sqlalchemy.orm import aliased
from walle.service.rbac.access import Access as AccessRbac
from flask import current_app


class UserModel(UserMixin, SurrogatePK, Model):
    # 表的名字:
    __tablename__ = 'user'

    current_time = datetime.now()
    password_hash = 'sadfsfkk'
    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    username = db.Column(String(50))
    is_email_verified = db.Column(Integer, default=0)
    email = db.Column(String(50), unique=True, nullable=False)
    password = db.Column(String(50), nullable=False)
    avatar = db.Column(String(100))
    role_id = db.Column(Integer, db.ForeignKey('role.id'), default=1)
    status = db.Column(Integer, default=1)
    role_info = relationship("walle.model.user.RoleModel", back_populates="users")
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    status_mapping = {
        0: '新建',
        1: '正常',
        2: '冻结',
    }

    def item(self, user_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        data = self.query.filter_by(id=self.id).first()
        return data.to_json() if data else []

    def update(self, username, role_id, password=None):
        # todo permission_ids need to be formated and checked
        user = self.query.filter_by(id=self.id).first()
        user.username = username
        user.role_id = role_id
        if password:
            user.password = generate_password_hash(password)

        db.session.commit()
        return user.to_json()

    def remove(self):
        """

        :param role_id:
        :return:
        """
        self.query.filter_by(id=self.id).delete()
        return db.session.commit()

    def verify_password(self, password):
        """
        检查密码是否正确
        :param password:
        :return:
        """
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def set_password(self, password):
        """Set password."""
        self.password = generate_password_hash(password)

    def general_password(self, password):
        """
        检查密码是否正确
        :param password:
        :return:
        """
        self.password = generate_password_hash(password)
        return generate_password_hash(password)


    def fetch_access_list_by_role_id(self, role_id):
        module = aliased(AccessModel)
        controller = aliased(AccessModel)
        action = aliased(AccessModel)
        role = RoleModel.query.get(role_id)
        access_ids = role.access_ids.split(',')

        data = db.session\
            .query(controller.name_en, controller.name_cn,
                   action.name_en, action.name_cn) \
            .outerjoin(action, action.pid == controller.id) \
            .filter(module.type == AccessModel.type_module) \
            .filter(controller.id.in_(access_ids)) \
            .filter(action.id.in_(access_ids)) \
            .all()


        return [AccessRbac.resource(a_en, c_en) for c_en, c_cn, a_en, a_cn in data if c_en and a_en]

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = UserModel.query
        if kw:
            query = query.filter(or_(UserModel.username.like('%' + kw + '%'), UserModel.email.like('%' + kw + '%')))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        user_list = [p.to_json() for p in data]
        return user_list, count

    def fetch_by_uid(self, uids=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = UserModel.query
        if uids:
            query = query.filter(UserModel.id.in_(uids))
        data = query.order_by('id desc').all()
        # current_app.logger.info(data)
        user_list = [p.to_json() for p in data]
        return user_list

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'is_email_verified': self.is_email_verified,
            'email': self.email,
            'avatar': self.avatar,
            'role_id': self.role_id,
            'status': self.status_mapping[self.status],
            'role_name': self.role_info.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


class AccessModel(SurrogatePK, Model):
    __tablename__ = 'access'

    type_module = 'module'
    type_controller = 'controller'
    type_action = 'action'

    status_open = 1
    status_close = 2
    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name_cn = db.Column(String(30))
    name_en = db.Column(String(30))
    pid = db.Column(Integer)
    type = db.Column(String(30))
    sequence = db.Column(Integer)
    archive = db.Column(Integer)
    icon = db.Column(String(30))
    fe_url = db.Column(String(30))
    fe_visible = db.Column(Integer)
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def menu(self, role):
        role_id = 1
        role = RoleModel(id=role_id).item()
        data = {}

        query = self.query.filter_by(fe_visible=1) \
            .filter(AccessModel.type.in_((self.type_module, self.type_controller))) \
            .filter(AccessModel.id.in_(role['access_ids'].split(','))) \
            .order_by('sequence asc') \
            .all()
        for item in query:
            if item.type == self.type_module:
                data[item.id] = {
                    'title': item.name_cn,
                    'icon': item.icon,
                }
            elif item.type == self.type_controller:
                if not data[item.pid].has_key('sub_menu'):
                    data[item.pid]['sub_menu'] = []
                data[item.pid]['sub_menu'].append({
                    'title': item.name_cn,
                    'icon': item.icon,
                    'fe_url': item.fe_url,
                })

        return data.values()

    def list(self):
        """
        获取分页列表
        :param page:
        :param size:
        :param kw:
        :return:
        """
        menus_module = {}
        menus_controller = {}
        module = aliased(AccessModel)
        controller = aliased(AccessModel)
        action = aliased(AccessModel)

        data = db.session.query(module.id, module.name_cn, controller.id, controller.name_cn, action.id, action.name_cn) \
            .outerjoin(controller, controller.pid == module.id) \
            .outerjoin(action, action.pid == controller.id) \
            .filter(module.type == self.type_module) \
            .all()
        for m_id, m_name, c_id, c_name, a_id, a_name in data:
            # module
            if not menus_module.has_key(m_id):
                menus_module[m_id] = {
                    'id': m_id,
                    'title': m_name,
                    'sub_menu': {},
                }
            # controller
            if not menus_module[m_id]['sub_menu'].has_key(c_id) and c_name:
                menus_module[m_id]['sub_menu'][c_id] = {
                    'id': c_id,
                    'title': c_name,
                    'sub_menu': {},
                }
            # action
            if not menus_controller.has_key(c_id):
                menus_controller[c_id] = []
            if a_name:
                menus_controller[c_id].append({
                    'id': a_id,
                    'title': a_name,
                })
        menus = []
        for m_id, m_info in menus_module.items():
            for c_id, c_info in m_info['sub_menu'].items():
                m_info['sub_menu'][c_id]['sub_menu'] = menus_controller[c_id]
            menus.append({
                'id': m_id,
                'title': m_info['title'],
                'sub_menu': m_info['sub_menu'].values(),
            })

        return menus

    def to_json(self):
        return {
            'id': self.id,
            'name_cn': self.name_cn,
            'name_en': self.name_en,
            'pid': self.pid,
            'type': self.type,
            'sequence': self.sequence,
            'archive': self.archive,
            'icon': self.icon,
            'fe_url': self.fe_url,
            'fe_visible': self.fe_visible,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


# 项目配置表
class RoleModel(UserMixin, SurrogatePK, Model):
    # 表的名字:
    __tablename__ = 'role'

    # current_time = datetime.now()
    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(30))
    access_ids = db.Column(Text, default='')
    users = relationship("UserModel", back_populates="role_info")

    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = RoleModel.query
        if kw:
            query = query.filter(RoleModel.name.like('%' + kw + '%'))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        list = [p.to_json() for p in data]
        return list, count

    def item(self, role_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        role_id = role_id if role_id else self.id
        data = RoleModel.query.filter_by(id=role_id).first()
        return data.to_json() if data else []

    def add(self, name, access_ids):
        # todo access_ids need to be formated and checked
        role = RoleModel(name=name, access_ids=access_ids)

        db.session.add(role)
        db.session.commit()
        self.id = role.id
        return self.id

    def update(self, name, access_ids, role_id=None):
        # todo access_ids need to be formated and checked
        role_id = role_id if role_id else self.id
        role = RoleModel.query.filter_by(id=role_id).first()
        role.name = name
        role.access_ids = access_ids

        return db.session.commit()

    def remove(self, role_id=None):
        """

        :param role_id:
        :return:
        """
        role_id = role_id if role_id else self.id
        RoleModel.query.filter_by(id=role_id).delete()
        return db.session.commit()

    def to_json(self):
        return {
            'id': self.id,
            'role_name': self.name,
            'access_ids': self.access_ids,
            'users': len(self.users),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }


# 项目配置表
class GroupModel(SurrogatePK, Model):
    __tablename__ = 'user_group'

    current_time = datetime.now()

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, db.ForeignKey('user.id'))
    # TODO
    # user_ids = db.relationship('walle.model.tag.TagModel', backref=db.backref('users'))
    group_id = db.Column(Integer, db.ForeignKey('tag.id'))
    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)
    group_name = None

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        group = GroupModel.query
        if kw:
            group = group.filter_by(TagModel.name.like('%' + kw + '%'))
        group = group.offset(int(size) * int(page)).limit(size).all()

        list = [p.to_json() for p in group]
        return list, 3

        user_ids = []
        group_dict = {}
        for group_info in group:
            user_ids.append(group_info.user_id)
            group_dict = group_info.to_json()

        group_dict['user_ids'] = user_ids
        # del group_dict['user_id']
        # return user_ids
        return group_dict

        query = TagModel.query
        if kw:
            query = query.filter(TagModel.name.like('%' + kw + '%'))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        list = [p.to_json() for p in data]
        return list, count

    def add(self, space_name, user_ids):
        tag = TagModel(name=space_name, label='user_group')
        db.session.add(tag)
        db.session.commit()
        current_app.logger.info(user_ids)

        for user_id in user_ids:
            user_group = GroupModel(group_id=tag.id, user_id=user_id)
            db.session.add(user_group)

        db.session.commit()
        if tag.id:
            self.group_id = tag.id

        return tag.id

    def update(self, group_id, group_name, user_ids):
        # 修改tag信息
        tag_model = TagModel.query.filter_by(label='user_group').filter_by(id=group_id).first()
        if tag_model.name != group_name:
            tag_model.name = group_name

        # 修改用户组成员
        group_model = GroupModel.query.filter_by(group_id=group_id).all()
        user_exists = []
        for group in group_model:
            # 用户组的用户id
            user_exists.append(group.user_id)
            # 表里的不在提交中,删除之
            if group.user_id not in user_ids:
                GroupModel.query.filter_by(id=group.id).delete()

        # 提交的不在表中的,添加之
        user_not_in = list(set(user_ids).difference(set(user_exists)))
        for user_new in user_not_in:
            group_new = GroupModel(group_id=group_id, user_id=user_new)
            db.session.add(group_new)

        db.session.commit()
        return self.item()

    def item(self, group_id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        #
        group_id = group_id if group_id else self.group_id
        tag = TagModel.query.filter_by(id=group_id).first()
        if not tag:
            return None
        tag = tag.to_json()

        group_id = group_id if group_id else self.group_id
        groups = GroupModel.query.filter_by(group_id=group_id).all()

        user_ids = []
        for group_info in groups:
            user_ids.append(group_info.user_id)

        current_app.logger.info(user_ids)
        user_model = UserModel()
        user_info = user_model.fetch_by_uid(uids=set(user_ids))
        # current_app.logger.info(user_info)


        tag['user_ids'] = user_ids
        tag['user_info'] = user_info
        tag['users'] = len(user_ids)
        return tag

        del group_dict['user_id']
        # return user_ids
        return group_dict
        return group.to_json()
        # group = group.to_json()

        users = UserModel.query \
            .filter(UserModel.id.in_(group['users'])).all()
        group['user_ids'] = [user.to_json() for user in users]

        return group

    def remove(self, group_id=None, user_id=None):
        """

        :param role_id:
        :return:
        """
        if group_id:
            GroupModel.query.filter_by(group_id=group_id).delete()
        elif user_id:
            GroupModel.query.filter_by(user_id=user_id).delete()
        elif self.group_id:
            GroupModel.query.filter_by(group_id=self.group_id).delete()

        return db.session.commit()

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'group_name': self.group_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

# 项目配置表
class SpaceModel(SurrogatePK, Model):
    # 表的名字:
    __tablename__ = 'space'
    current_time = datetime.now()
    status_close = 0
    status_open = 1

    # 表的结构:
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer)
    group_id = db.Column(Integer)
    name = db.Column(String(100))
    status = db.Column(Integer)

    created_at = db.Column(DateTime, default=current_time)
    updated_at = db.Column(DateTime, default=current_time, onupdate=current_time)

    def list(self, page=0, size=10, kw=None):
        """
        获取分页列表
        :param page:
        :param size:
        :return:
        """
        query = self.query
        if kw:
            query = query.filter(SpaceModel.name.like('%' + kw + '%'))
        count = query.count()
        data = query.order_by('id desc').offset(int(size) * int(page)).limit(size).all()
        list = [p.to_json() for p in data]
        return list, count

    def item(self, id=None):
        """
        获取单条记录
        :param role_id:
        :return:
        """
        id = id if id else self.id
        data = self.query.filter_by(id=id).first()

        if not data:
            return []

        data = data.to_json()

        return data

    def add(self, *args, **kwargs):
        # todo permission_ids need to be formated and checked
        data = dict(*args)

        tag = TagModel(name=data['name'], label='user_group')
        db.session.add(tag)
        db.session.commit()

        user_group = GroupModel(group_id=tag.id, user_id=data['user_id'])
        db.session.add(user_group)
        db.session.commit()

        data['group_id'] = tag.id
        space = SpaceModel(**data)

        db.session.add(space)
        db.session.commit()
        self.id = space.id

        return self.id

    def update(self, *args, **kwargs):
        # todo permission_ids need to be formated and checked
        # a new type to update a model

        update_data = dict(*args)
        return super(SpaceModel, self).update(**update_data)

    def remove(self, space_id=None):
        """

        :param space_id:
        :return:
        """
        space_id = space_id if space_id else self.id
        SpaceModel.query.filter_by(id=space_id).update({'status': self.status_close})
        return db.session.commit()

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }



@login_manager.user_loader
def load_user(user_id):
    user = UserModel.query.get(user_id)
    role = RoleModel().item(user.role_id)
    access = UserModel().fetch_access_list_by_role_id(user.role_id)
    # logging.error(RoleModel.query.get(user.role_id).access_ids)
    # logging.error(role['access_ids'].split(','))
    # logging.error(UserModel.query.get(user_id))
    return UserModel.query.get(user_id)
