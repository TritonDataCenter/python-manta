# python-manta Changelog

## 1.1.0 (not yet released)

- Add `manta.CLISigner` for signing appropriate for an CLI tool. It will
  use an ssh-agent if available and fallback to using a given SSH key
  (looking at key files in "~/.ssh/" as appropriate). Switch `mantash`
  to use this for signing.

- Fix a bug where the '-type' argument to 'mantash find' always returned empty
  results.

- Add 'mantash -C DIRECTORY' to start in the given directory. E.g.:

        mantash -C /trent/public find .

- Add support for MANTASH_PS1 envvar for a fancy prompt. A subset of the
  Bash codes are supported (see "PROMPTING" section in `man bash and
  the `_update_prompt` method in "bin/mantash"). The default is `[\m\w]$ `,
  but you might like:

        export MANTASH_PS1='\e[90m[\u@\h \e[34m\w\e[90m]$\e[0m '

- `mantash --version`


## 1.0.0

First release.
