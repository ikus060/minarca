# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Jan 30, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

import time
from base64 import b64encode

import pkg_resources
from rdiffweb.core.model import UserObject

import minarca_server
import minarca_server.tests
from minarca_server.core.minarcaid import gen_minarcaid_v1

private_key = b"""-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAtC7N4D1f7d+XVDgI+hSVz908CYQGo0DLMd4KD0aeBiBJjseh
SrPiAsOvyqOXHir9yJkADz7JGBvo3Q9JxPr3ukQX0ZmNonwOUE9lmdsPt6/+Qk+l
eenTwWz5N49Mi9ZdqHXRRi86pT+yrGMrrd9DHj/DyyotRvu9YY6R3jYUgw9cYSC8
3pRmvpm5X91EXhQLYsZZFnMrprp1X3xGg9IZT9J9oKm08XzoxrzzidNiRZzuK3hp
Nb/vTkklK+4ADRGEiNXfQYg0QaabDluh+cGhfpgm3KpjAIAAhp3/t6EbBnrv5f0C
MK5RXGIe9M5nMTeSlu9W4+8Fr3CTTTHM9aUExQIDAQABAoIBAAeOWusyHQlrB1FB
1FE1zHPeHDwYlvVWV0RtF6Y9A4164dAksQU39py/u2nXuGj3IT4TTyb/LrcIce3V
9qBVwfkZYpeomoGbiuIf95Z0faaUsSieEcYYtzJKW/J825dAUxx9wbFGyRfQTFw3
AHLshPJfdtot7PN9b8YH5jgXs9PXHqzr0f6+J8cU2NJpvCEJjbSHAwDfdEmggXq0
8W8WpEKdyF8n3wAM9wv56Vxv4VV8thf9rqHdEkzoLUl7On29L5bxwk4aLZ4RrftG
STLULmBCKf/fzYY+DriVqitwk0jXJxJ1rPH8Mi37wHcovZ6FAMWLZG6lVeV420Q/
FTas9tUCgYEA5swCXqj3g03elSlsCamGtloT6WeJ2p4cj2xDDu3ScN1k7g8H3JCC
hXqu6iGVF7AndHtbyVPkY/rwJ7lzWIWxiKqvmhckDKlChsbvD0YfZA6nEn0y2jPf
xZK2ZElpzuVGccbwaWPHmvyTXR3wnNEZEmKXzMmtDm/0roZqciE++R8CgYEAx9vd
S/5E8J06c6yYLTBn0VjcdVhNxsuf4B/FTDMZpQnhr4Yu+uG2AjZDIWAt20z0eWe5
5HMx8EygqhTBgtTvRqco+rERfzlSaFVPKBF9rRR7mMNG96vodDWpcEsnfO5mJfpX
cxt5L9Jar0+wulRy5W+Jj8/it/zgJQHtAW5C8ZsCgYAkoOILZeOKSjR2FdHYorgH
frpEQ7NkJ82+kV7/Io1QbkKTaX1E6wZb6sGR1OyVitZoLR+/DvpjR7MPiuYceXNY
jkY6PUvyWnZ9b1sHYIig15Z6X7ZPXQY5k/QwbFpHhKmuavVCtJw8I7O7hoHmUWUa
Pt16mdNGRExf2mNQY6hb3wKBgEvpolPkH9F5FyOq0h6P/U8SPqK/yMMSwwZBaxJ3
cm0ypKuj/yJCK30JmVQLET/0KgQXNw+kBbrtkDUqLxp/wOcIRVN7gFbfsgJ5LNje
U+szFYM/4Svf+ypw24wQr84PS3NvdFn/fHeCoflm/oy32PB2/jxGzSnvfj/wTFK3
y+uzAoGAaajYr0oymqU1zXa88+9L7lM9w7Lbpilt033bAtemDO+vk2kcHYWiDkJa
+ZggECiWTJAH4gY5Q04Xd6OAe6F6O8d5O944W7XQZ51+X/3hsVQkt8hvy9gBXeSv
AeirEw3X/Tv/Js1MZLZPJNGJxG5/zb/yWYbz8+edh6WtyeNJW9Y=
-----END RSA PRIVATE KEY-----
"""
public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0Ls3gPV/t35dUOAj6FJXP3TwJhAajQMsx3goPRp4GIEmOx6FKs+ICw6/Ko5ceKv3ImQAPPskYG+jdD0nE+ve6RBfRmY2ifA5QT2WZ2w+3r/5CT6V56dPBbPk3j0yL1l2oddFGLzqlP7KsYyut30MeP8PLKi1G+71hjpHeNhSDD1xhILzelGa+mblf3UReFAtixlkWcyumunVffEaD0hlP0n2gqbTxfOjGvPOJ02JFnO4reGk1v+9OSSUr7gANEYSI1d9BiDRBppsOW6H5waF+mCbcqmMAgACGnf+3oRsGeu/l/QIwrlFcYh70zmcxN5KW71bj7wWvcJNNMcz1pQTF"

other_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCW57OtjjiGAVCtxIOrW7MhIYh9GaiijQ3GItPQA/Mn9fQpW/gzkW3+hKkbq9YdBCHUBh9tH/9H7Q5+nNE9btA+ROWwK2m+j12dm7KYmnoRrhO42sHOe1rivfNSmlvHgiBHHHyMPfa/BDa8rJCpLT17D2gA5aBBudihXNe0YwcMKuDVT5EeIUOPSz+zMdBxFlaQ4Bno70Ml9ACZFMqLuTgP0tGM8ec4x54Bl3LcnqHQ9tK5EMInf6BChBDhPN3tW9ZxRwnURhay2CPovFCJw6RL66uqqX+mz1AD8SKwdgGtpm1clZj/AwtqMzckV4mnpaQ3NrCbPLalek0+kHd7j8Xn"


class MinarcaApplicationTestWithHelpUrl(minarca_server.tests.AbstractMinarcaTest):
    default_config = {'minarca-help-url': 'https://example.com/help/'}

    def test_get_help(self):
        # Check if the URL can be changed
        self.getPage("/help")
        self.assertStatus(303)
        self.assertHeader('Location', 'https://example.com/help/')


class MinarcaApplicationTestWithRemoteIdentity(minarca_server.tests.AbstractMinarcaTest):
    basic_headers = [("Authorization", "Basic " + b64encode(b"admin:admin123").decode('ascii'))]

    default_config = {
        'minarca-remote-host': "test.examples:2222",
        'minarca-remote-host-identity': pkg_resources.resource_filename('minarca_server.tests', ''),
    }

    def test_get_api_minarca_identity(self):
        data = self.getJson("/api/minarca/", headers=self.basic_headers)
        self.assertIn("[test.examples]:2222", data['identity'])

    def test_get_bg_jpg(self):
        self.getPage("/static/bg.jpg")
        self.assertStatus(200)


class MinarcaApplicationTestMinarcaId(minarca_server.tests.AbstractMinarcaTest):
    def test_api_currentuser_with_valid_minarcaid(self):
        # Given a user with a public SSH key
        user = UserObject.add_user('bob')
        user.commit()
        user.add_authorizedkey(key=public_key, comment="test@mysshkey")
        user.add_authorizedkey(key=other_public_key, comment="my-other-key@mysshkey")
        user.commit()
        # Given a valid minarcaid
        minarcaid = gen_minarcaid_v1(private_key)
        # When querying current user API with minarcaid
        headers = [("Authorization", f"Minarcaid {minarcaid}")]
        self.getPage('/api/currentuser/', headers=headers)
        # Then data is return without error
        self.assertStatus(200)

    def test_api_currentuser_with_expired_minarcaid(self):
        # Given a user with a public SSH key
        user = UserObject.add_user('bob')
        user.commit()
        user.add_authorizedkey(key=public_key, comment="test@mysshkey")
        user.commit()
        # Given an expired minarcaid
        minarcaid = gen_minarcaid_v1(private_key, epoch=int(time.time()) - 305)
        # When querying current user API with minarcaid
        headers = [("Authorization", f"Minarcaid {minarcaid}")]
        self.getPage('/api/currentuser/', headers=headers)
        # Then data is return without error
        self.assertStatus(401)

        # Given an epoch in future minarcaid
        minarcaid = gen_minarcaid_v1(private_key, epoch=int(time.time()) + 305)
        # When querying current user API with minarcaid
        headers = [("Authorization", f"Minarcaid {minarcaid}")]
        self.getPage('/api/currentuser/', headers=headers)
        # Then data is return without error
        self.assertStatus(401)

    def test_api_currentuser_with_invalid_minarcaid(self):
        # Given a user with a public SSH key
        user = UserObject.add_user('bob')
        user.commit()
        user.add_authorizedkey(key=other_public_key, comment="test@mysshkey")
        user.commit()
        # Given an minarcaid generate with a different private key.
        minarcaid = gen_minarcaid_v1(private_key)
        # When querying current user API with minarcaid
        headers = [("Authorization", f"Minarcaid {minarcaid}")]
        self.getPage('/api/currentuser/', headers=headers)
        # Then data is return without error
        self.assertStatus(401)
