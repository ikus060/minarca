#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Dec 8, 2020

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

import argparse
import subprocess
import sys


class ZFSQuotaException(Exception):
    pass


def _parse_args(args):
    parser = argparse.ArgumentParser(
        prog='minarca-zfs-quota',
        description='Minarca utilities to get and set ZFS quota. If VALUE is define, sets the given quota',
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-P', '--project', help="Set project quotas for named project.")
    group.add_argument('-u', '--user', help="Set user quotas for named user. This is the default.")
    group.add_argument('-g', '--group', help="Set group quotas for named group.")
    parser.add_argument('pool', nargs=1)
    parser.add_argument('quota', nargs='?', help="If defined, sets the quota to the given value.")
    return parser.parse_args(args)


def is_project_quota_enabled(pool):
    # Get value using zfs (as exact value).
    args = ['/sbin/zpool', 'get', '-p', '-H', '-o', 'value', 'feature@project_quota', pool]
    try:
        output = subprocess.check_output(args, encoding='ascii', stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output
    except Exception as e:
        output = str(e)
    # Should be active or enabled.
    return output in ['enabled', 'active']


def get_quota(pool, projectid=None):
    """Get user disk quota and space."""
    assert pool
    assert projectid and isinstance(projectid, int), "projectid must be a number " + projectid
    args = [
        '/sbin/zfs',
        'get',
        '-p',
        '-H',
        '-o',
        'value',
        'projectused@%s,projectquota@%s' % (projectid, projectid),
        pool,
    ]

    # Get value using zfs (as exact value).
    try:
        output = subprocess.check_output(args, encoding='ascii', stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise ZFSQuotaException(e.output)
    except Exception as e:
        output = str(e)

    values = output.splitlines()
    if len(values) != 2:
        raise ZFSQuotaException('fail to get user disk space: %s' % (output,))
    used, quota = [0 if x == '-' else int(x) for x in values]

    # Return quota value if defined.
    if quota:
        return {"size": quota, "used": used}
    # Return 0 for unlimited quota.
    return {"size": 0, "used": 0}


def set_quota(pool, quota, projectid=None):
    """Update the user quota. Return True if quota update is successful."""
    assert pool
    assert quota and isinstance(quota, int), "quota must be a number " + quota
    assert projectid and isinstance(projectid, int), "projectid must be a number " + projectid
    args = ['/sbin/zfs', 'set', 'projectquota@%s=%s' % (projectid, quota), pool]
    try:
        subprocess.check_output(args, encoding='ascii', stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise ZFSQuotaException(e.output)
    except Exception as e:
        raise ZFSQuotaException(str(e))


def main(args=None):
    # Parse arguments
    args = _parse_args(sys.argv[1:] if args is None else args)
    try:
        if args.quota is None:
            values = get_quota(pool=args.pool[0], projectid=args.project)
            print("%s\t%s\t%s" % (args.project or args.user or args.group, values['used'], values['quota']))
        else:
            set_quota(pool=args.pool[0], quota=args.quota, projectid=args.project)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == '__main__':  # Script executed directly?
    main()
