# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import argparse
import grp
import pwd
import sys

import pkg_resources
from rdiffweb.core.config import get_parser as get_rdiffweb_parser

# Get rdiffweb version.
try:
    VERSION = pkg_resources.get_distribution("minarca_server").version
except pkg_resources.DistributionNotFound:
    VERSION = "DEV"


def user(user_name):
    """
    Verify if the given string is a valid username
    """
    try:
        return pwd.getpwnam(user_name).pw_uid
    except KeyError:
        raise ValueError(user_name)


def group(group_name):
    """
    Verify if the given stirng is a valid group.
    """
    try:
        return grp.getgrnam(group_name).gr_gid
    except KeyError:
        raise ValueError(group_name)


def get_parser():
    """
    Extends Rdiffweb parser.
    """
    parser = get_rdiffweb_parser()
    parser.prog = 'minarca-server'
    parser.description = 'Web server to browse and restore backups.'

    parser.add(
        '--minarca-user-dir-mode',
        '--minarcauserdirmode',
        metavar='MODE',
        help=argparse.SUPPRESS,
        type=int,
        default=0o0770,
    )

    parser.add(
        '--minarca-user-dir-owner',
        '--minarcauserdirowner',
        type=user,
        metavar='OWNER',
        help=argparse.SUPPRESS,
        default='minarca',
    )

    parser.add(
        '--minarca-user-dir-group',
        '--minarcauserdirgroup',
        type=group,
        metavar='GROUP',
        help=argparse.SUPPRESS,
        default='minarca',
    )

    parser.add(
        '--minarca-user-base-dir',
        '--minarcauserbasedir',
        '--minarcausersetupbasedir',
        metavar='FOLDER',
        help="""base directory where all the backup should reside. Any
            user_root outside this repository will be refused.""",
        default='/backups/',
    )

    parser.add(
        '--minarca-restricted-to-base-dir',
        '--minarca-restricted-to-based-dir',
        '--minarcarestrictedtobaseddir',
        action='store_true',
        help=argparse.SUPPRESS,
        default=True,
    )

    parser.add(
        '--minarca-shell',
        '--minarcashell',
        metavar='FILE',
        help="""location of minarca-shell to be used to handle SSH
            connection. This is used to configure `authorized_keys` to
            restrict SSH command line to be executed""",
        default='/opt/minarca-server/bin/minarca-shell',
    )

    parser.add(
        '--minarca-auth-options',
        '--minarcaauthoptions',
        metavar='OPTIONS',
        help="""authentication option to be passed to `authorized_keys`.
            This is used to limit the user's permission on the SSH Server,
            effectively disabling X11 forwarding, port forwarding and PTY.""",
        default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty',
    )

    parser.add(
        '--minarca-remote-host',
        '--minarcaremotehost',
        metavar='HOST:PORT',
        help="""the remote SSH identity. This value is queried by Minarca
            Client to link and back up to the server. If not provided, the
            HTTP URL is used as a base. You may need to change this value
            if the SSH server is accessible using a different IP address
            or if not running on port 22. e.g.: ssh.example.com:2222""",
    )

    parser.add(
        '--minarca-remote-host-identity',
        '--minarcaremotehostidentity',
        metavar='FOLDER',
        help="""location of SSH server identity. This value is queried by
            Minarca Client to authenticate the server. You may need to
            change this value if SSH service and the Web service are not
            running on the same server.""",
        default="/etc/ssh",
    )

    parser.add(
        '--minarca-help-url',
        '--minarcahelpurl',
        metavar='URL',
        help="""custom URL where to redirect user clicking on help button""",
        default="https://www.ikus-soft.com/en/support/#form",
    )

    parser.add(
        '--minarca-rdiff-backup-extra-args',
        '--rdiffbackup-args',
        metavar='ARGS',
        help="""list of extra argumenst to be pass to rdiff-backup server. e.g.: --no-compression""",
    )

    parser.add('--minarca-quota-api-url', '--minarcaquotaapiurl', metavar='URL', help="url to minarca-quota-api server")

    # Replace --version
    parser.conflict_handler = 'resolve'
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    # Replace default config file
    parser._default_config_files = ['/etc/minarca/minarca-server.conf', '/etc/minarca/conf.d/*.conf']

    # Override a couple of arguments with Minarca.
    parser.set_defaults(
        database_uri='/etc/minarca/rdw.db',
        default_theme='blue',
        favicon=pkg_resources.resource_filename(__name__, 'minarca.ico'),  # @UndefinedVariable
        footer_name='Minarca',
        footer_url='https://www.ikus-soft.com/en/minarca/',
        header_name='Minarca',
        header_logo=pkg_resources.resource_filename(__name__, 'minarca_22.png'),  # @UndefinedVariable
        log_access_file='/var/log/minarca/access.log',
        log_file='/var/log/minarca/server.log',
        welcome_msg={
            '': 'A <b>free and open-source</b> backup software providing end-to-end integration to put you in control of your backup strategy.<br/><br/><a href="https://www.ikus-soft.com/en/minarca/">website</a> • <a href="https://www.ikus-soft.com/en/minarca/doc/">docs</a> • <a href="https://groups.google.com/d/forum/minarca">community</a>',
            'fr': 'Un logiciel de sauvegarde <b>gratuit et à code source ouvert</b> fournissant une intégration bout en bout pour vous permettre de contrôler votre stratégie de sauvegarde.<br/><br/> <a href="https://www.ikus-soft.com/fr/minarca/">site web</a> • <a href="https://www.ikus-soft.com/fr/minarca/doc/">documentations</a> • <a href="https://groups.google.com/d/forum/minarca">communauté</a>',
        },
    )
    return parser


def parse_args(args=None, config_file_contents=None):
    args = sys.argv[1:] if args is None else args
    return get_parser().parse_args(args, config_file_contents=config_file_contents)
