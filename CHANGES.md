# python-manta Changelog

## 1.2.2 (not yet released)

- [pull #5] Add `-h` support for human readable sizes to `mantash ls`.
  (by Bill Pijewski).

- `mantash gzcat PATHS...`

- [issue #4] Fix possible infinite loop on `ls /:user/jobs`.


## 1.2.1

- Fix `job` handling of PATHS: relative paths within a dir, e.g.:

        $ job a-dir/a-file.txt ^ cat

  resulted bogus manta object paths (keys) being added to the job.

- Mantash `find` takes multiple DIRS, e.g. `find foo bar -type o`.

- Mantash `ls` fixes.

- Get tab-completion of paths to handle '~' properly.

- `cd -` support in mantash shell.

- Fix `mantash find OBJECT-PATH` (as opposed to find on a *DIR*).


## 1.2.0

- [issue #1] Drop the binary Crypto build for sunos-py27 (32-bit) and give
  instructions to install PyCrypto with pkgin et al on SmartOS.

- Improve tab-completion in the mantash interactive shell. It should now
  properly do manta path (e.g. `ls`), manta dir (e.g. `cd`), local path (e.g.
  `lls`), or local dir completion (e.g. `lcd`) depending on the command being
  used.

  Note that `get` does manta path completion and `put` does local path
  completion even though that is the inappropriate context for the *last* arg
  to those commands. The problem is that both `get` and `put` can accept
  multiple source paths if the last arg is a target *directory*. There is no
  good way to recognize when the last arg is being tab-completed.

- 'DST-PATH' in `mantash get SRC-PATH DST-PATH` now defaults to the cwd.


## 1.1.0

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
