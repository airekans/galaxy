# -*- coding:utf-8 -*-
# Copyright (c) 2015, Galaxy Authors. All Rights Reserved
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Author: wangtaize@baidu.com
# Date: 2015-03-30
from django.conf import urls

#views
urlpatterns = urls.patterns("console.quota.views",
        (r'^info','my_quota'),
        (r'^mygroups','my_group'),
        (r'^groupstat','group_stat'),

)

