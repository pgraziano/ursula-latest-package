# encoding: utf-8
# license: Apache 2.0
# title '{{ item }} controls'


{% if inspec.controls[item].skip_controls|default([])|length > 0 %}
include_controls "{{ inspec.profiles[inspec.controls[item].profile].name }}" do
{% for control in inspec.controls[item].skip_controls %}
    skip_control "{{ control }}"
{% endfor %}
end
{% elif inspec.controls[item].required_controls|default([])|length > 0 %}
require_controls "{{ inspec.profiles[inspec.controls[item].profile].name }}" do
{% for control in inspec.controls[item].required_controls %}
    control "{{ control }}"
{% endfor %}
end
{% else %}
include_controls "{{ inspec.profiles[inspec.controls[item].profile].name }}" do
end
{% endif %}
