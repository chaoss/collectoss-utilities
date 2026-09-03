# collectoss-utilities
Utilities for one-off repairs and recovery for CollectOSS instances

This project is a python CLI utility that implements scripts that aid operators of instances with making repairs.

For example, if a bug in data collection has left your instance with some corrupted data, you will likely be provided with a command to run from this script.


## Running

### Common issues

#### Missing environment variables

running with UV will have its own shell environment so environment variables available in your terminal wont automatically pass through.

use `uv run --env-file=".env"` to ensure the env vars are present in the environment. Note that UV doesnt do `ENV_VARS="WITH ${SUBSTITUTIONS}"`

#### Kerberos

If you are on a machine with valid kerberos tokens, but do not use kerberos to auth with your database, ensure the `?gssencmode=disable` flag is present at the end of your DB connection string
