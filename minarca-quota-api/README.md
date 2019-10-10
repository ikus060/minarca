# Minarca Quota API

This component provide a very basic RESTful API to access and update the user
quota defined on the storage server. This component is provided to allow
minarca/rdiffweb to be isolated from the persistence.

## Installation

This component need to e installed on a storage server with zfs. `zfs` need to
be available at `/sbin/zfs`.