# -*- coding: utf-8 -*-
"""

    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-03-25 11:15:01
    :author: wushuiyong@walle-web.io
"""
from flask import request
from walle.api.api import SecurityResource
from walle.service.deployer import Deployer


class RepoAPI(SecurityResource):
    def get(self, method, commit=None):
        """
        fetch project list or one item
        /project/<int:project_id>

        :return:
        """
        super(RepoAPI, self).get()
        project_id = request.args.get('project_id', '')

        if method == 'tags':
            return self.tags(project_id=project_id)
        elif method == 'branches':
            return self.branches(project_id=project_id)
        elif method == 'commits':
            branch = request.args.get('branch', '')
            return self.commits(project_id=project_id, branch=branch)
        return self.list_json(list=[])

    def tags(self, project_id=None):
        """
        fetch project list or one item
        /tag/

        :return:
        """
        wi = Deployer(project_id=project_id)
        tag_list = wi.list_tag()
        tags = tag_list.stdout.strip().split('\n')
        return self.render_json(data={
            'tags': tags,
        })

    def branches(self, project_id=None):
        """
        fetch project list or one item
        /tag/

        :return:
        """
        wi = Deployer(project_id=project_id)
        branches = wi.list_branch()
        return self.render_json(data={
            'branches': branches,
        })

    def commits(self, project_id, branch):
        """
        fetch project list or one item
        /tag/

        :return:
        """
        wi = Deployer(project_id=project_id)
        commits = wi.list_commit(branch)

        return self.render_json(data={
            'branches': commits,
        })
