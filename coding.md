# Ursula Developer Coding Standards
In the beginning, there were no guidelines. And it was good. But that
didn't last long. As more and more people added more and more code,
we realized that we needed a set of coding standards to make sure that
Ursula at least *attempted* to display some form of consistency.

In addition, newer versions of Ansible will change what format these
files can be, so we are being proactive with a coding style to prevent
having to clean up more things when we move to new versions of Ansible.

Thus, these coding standards/guidelines were developed. Note that not
all of Ursula adheres to these standards just yet. Some older code has
just not been changed yet. But be clear, all new code *must* adhere to
these guidelines.

Below are the patterns that we expect Ursula developers to follow.

## General
* Our chosen file extension for YAML files is `.yml`.

* Make every attempt to keep lines under 80 chars long.

## Variables
* When referencing variables with mustache brackets, use spaces around the
  brackets: `"{{ a_var }}"`. 

* Do not use "bare variables" in `with_items`. Instead quote them:
  `with_items: "{{ nova.list_var }}"`. The use of bare variables in a
  loop definition is deprecated in Ansible 2.0.

* Use descriptive varibles when setting facts or registering output. Do not
  use the same variable name used elsewhere within Ursula.

* Boolean variables should always be run through the `|bool` filter to
  normalize the input into a Boolean.

* Do not rely on variable settings in an example env defaults file. These
  files are just for example and may not be used in production. Instead rely
  on role defaults or the `|default()` filter to set a default value.

* Filter application should be done with spaces between the variable,
  the pipe symbol, and the filter name: `{{ foo | default(False) | bool }}`

* Be aware of jinja2 python object method capabilities when deciding on
  variable names. Avoid any variable name that could be confused with an
  object method (like endswith, startswith, split, upper, index, count).

## Tasks
* When possible, use full YAML syntax (`key: value`) for task arguments,
  instead of `key=value` pairs. Some task inputs will require full yaml,
  it is better to be consistent across the playbooks. This full syntax is
  also known as "complex arguments".

* When writing a task that notifies handlers, the notify statement should be
  last. Any tags above the notify. Any loop statement should come just before
  the tags, and any conditional should go above that.

  ```
  - name: this is a task
    a_module:
      arg1: value
      arg2: "{{ templated_value }}"
    with_items:
      - "{{ a_big_ole_list }}"
    tags:
      - herp
      - derp
    notify:
      - a handler
  ```

* Task names must not use variables in them.

* All Tasks, Plays, and Handlers must have a name.

* Do not use `ignore_errors`, instead use `failed_when: false`. Use of
  `failed_when`  prevents red output from being shown on screen, which makes
  debugging to find the real fatal error easier.

* Tasks which just gather data and do not cause change should not register
  "change" from ansible point of view. Make use of `changed_when: False`.

* No tasks should prompt the user for interaction. The intention of Ursula
  is to run completely non-interactive.

* Tag expression should be either a single word `tags: thistag`, or a YAML
  list of tags to apply with each tag on a new line. Do not use `tags=foo`,
  particularly when including a task file.

* Do not rely on a when conditional to identify that a loop variable is
  undefined to avoid the task. Use a filter to default the variable to an
  empty list: `with_items: "{{ foo|default([]) }}"`

* When delegating a task to another host (or localhost), use the task
  control `delegate_to:`. Do not make use of `local_action:` as it changes
  the format of a task definition, requiring the module name to be moved.

## Roles
* Role dependencies have a cost. Be wary of introducing a new role
  dependency, particularly if it could be run from many plays, or if the
  dependency role includes a large number of tasks.

* Task file includes from a role's `tasks/main.yml` should be avoided
  unless there is a desire to apply a tag or a conditional to an entire
  set of logically grouped tasks.

* Role defaults must be namespaced to the role. No top-level role variable
  definitions are allowed.

## Modules
* Prefer the command module over the shell module.

* Files are put in place via the template module, rather than copy, so that
  all the input files that go to a system are gathered in the same directory
  (`templates/`)

* Directory structure within templates/ must match (as close as possible) the
  destination path of the file in question. e.g. if the destination is
  `/etc/nova/nova.conf`, the file would live in `templates/etc/nova/nova.conf`
  (note the lack of `.j2` suffix)

## Testing
* When adding new features to Ursula, it is desireable that they are
  feature flagged in a way to prevent immediate implementation of the
  feature in existing installs.

* That said, when at all possible it is desireable for our CI runs to
  at least exercise the Ansible code used to deliver a new feature, even if
  the feature itself is not tested in CI.

* Be cognizant of CI runtimes. The more tests, the longer the run, the slower
  the changes will flow. Try to balance good coverage with quick tests for
  CI runs.
