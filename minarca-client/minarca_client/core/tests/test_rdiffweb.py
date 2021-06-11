# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.core import Rdiffweb
import os
import responses  # @UnresolvedImport
import tempfile
import unittest

IDENTITY = """[test.minarca.net]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Qng4S5d75rtYxklVdIkPiz4paf2pdnCEshUoailQO root@sestican
[test.minarca.net]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCi0uz4rVsLpVl8b6ozYzL+t1Lh9P98a0tY7KqAtzFupjtZivdIYxh6jXPeonYo7egY+mFgMX22Tlrth8woRa2M= root@sestican
[test.minarca.net]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+XU4xipQJUKqGshBeCBH7vNfeDgIOXQeaz6Q4S9QbWM39gTUedCfQuabUjXUJafPX8RfEe2xKALaHOdHzT1HYq3GL8oUa4C1J3xkabnZbxA06Ko4Ya31S84G/S+L8kwZ7PmxegZedk6Za49uxBjl/2lBQM4B/BgNccQ9Ifu5Kw4gmU6mfIOZxJ9qx0rF87cXXi5b6o7GMNbK6UViheZvyJQNuR8oYdMEqaVyezJGfSOEFWPm+mQm19Tu4Ad9ElyMyA8SImQshOz7YupEeb26sLvvVwl0EyirMwlI8NIt66DGEy5s2egorL3COB+L0Yp2wjLvzHBMr0Dwb/ZLJfbGR root@sestican
"""


class TestRdiffweb(unittest.TestCase):

    @responses.activate
    def setUp(self):
        responses.add(responses.GET, "http://localhost/")
        self.rdiffweb = Rdiffweb('http://localhost', 'admin', 'admin123')
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    @responses.activate
    def test_get_current_user_info(self):
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            body='{"email": "admin@example.com", "username": "admin", "repos": []}')
        data = self.rdiffweb.get_current_user_info()
        self.assertEqual("admin@example.com", data['email'])
        self.assertEqual("admin", data['username'])
        self.assertEqual([], data['repos'])

    @responses.activate
    def test_add_ssh_key(self):
        responses.add(
            responses.POST,
            "http://localhost/prefs/sshkeys/")
        self.rdiffweb.add_ssh_key('coucou', 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpGT3vU6FBQ6fsd4Ph/Bs9UtCqJS2OgR2s53Ud1YSsPSGU6hbowh/KJT5RtN7XIoXT4JI28sHH/HodkaG1g6G3320YPD6KNJPoFxEhl5tCFCqrORD98nBO9bJBTtldHAtNTrQXPFx04PeHMrm58We9tCe6xaSt4udLxQScv+r6F1iSgEfGTuYS7/XT/1n4KMHciPeFADWpN5Vd8aj+c//xJY+DvAoyGGu5VhSqg2QBsr/D56h9Xxwtau/zrFlTnEe1yx9ar2udMGgOjUmh4Um/EOLyBWpqQERnbdENATeUtiGssmsxDoC8JBMhAz+mP8bMTm23ZS2VXysT3Qz/mUEt')
        self.assertEqual(
            'action=add&title=coucou&key=ssh-rsa+AAAAB3NzaC1yc2EAAAADAQABAAABAQCpGT3vU6FBQ6fsd4Ph%2FBs9UtCqJS2OgR2s53Ud1YSsPSGU6hbowh%2FKJT5RtN7XIoXT4JI28sHH%2FHodkaG1g6G3320YPD6KNJPoFxEhl5tCFCqrORD98nBO9bJBTtldHAtNTrQXPFx04PeHMrm58We9tCe6xaSt4udLxQScv%2Br6F1iSgEfGTuYS7%2FXT%2F1n4KMHciPeFADWpN5Vd8aj%2Bc%2F%2FxJY%2BDvAoyGGu5VhSqg2QBsr%2FD56h9Xxwtau%2FzrFlTnEe1yx9ar2udMGgOjUmh4Um%2FEOLyBWpqQERnbdENATeUtiGssmsxDoC8JBMhAz%2BmP8bMTm23ZS2VXysT3Qz%2FmUEt',
            responses.calls[0].request.body)

    @responses.activate
    def test_get_minarca_info(self):
        responses.add(
            responses.GET,
            "http://localhost/api/minarca/",
            body='{"version": "3.9.1", "remotehost": "test.minarca.net:2222", "identity": "[test.minarca.net]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Qng4S5d75rtYxklVdIkPiz4paf2pdnCEshUoailQO root@sestican\\n[test.minarca.net]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCi0uz4rVsLpVl8b6ozYzL+t1Lh9P98a0tY7KqAtzFupjtZivdIYxh6jXPeonYo7egY+mFgMX22Tlrth8woRa2M= root@sestican\\n[test.minarca.net]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+XU4xipQJUKqGshBeCBH7vNfeDgIOXQeaz6Q4S9QbWM39gTUedCfQuabUjXUJafPX8RfEe2xKALaHOdHzT1HYq3GL8oUa4C1J3xkabnZbxA06Ko4Ya31S84G/S+L8kwZ7PmxegZedk6Za49uxBjl/2lBQM4B/BgNccQ9Ifu5Kw4gmU6mfIOZxJ9qx0rF87cXXi5b6o7GMNbK6UViheZvyJQNuR8oYdMEqaVyezJGfSOEFWPm+mQm19Tu4Ad9ElyMyA8SImQshOz7YupEeb26sLvvVwl0EyirMwlI8NIt66DGEy5s2egorL3COB+L0Yp2wjLvzHBMr0Dwb/ZLJfbGR root@sestican\\n"}')
        data = self.rdiffweb.get_minarca_info()
        self.assertEqual("3.9.1", data['version'])
        self.assertEqual("test.minarca.net:2222", data['remotehost'])
        self.assertEqual(IDENTITY, data['identity'])


if __name__ == "__main__":
    unittest.main()
