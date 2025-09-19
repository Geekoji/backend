{{/*
Generating credentials.yaml from .Values.secrets.
Iterates over .Values.pgbouncer.config.databases,
finds matching `_DB_PASSWORD` suffix in .Values.secrets,
and outputs a YAML mapping of database -> { user, password }.
*/}}
{{- define "pgbouncer.credentials" }}
{{- $secrets := .Values.secrets }}
{{- $out := dict }}
{{- range $db, $_ := .Values.pgbouncer.config.databases }}
  {{- $user := regexReplaceAll "-db" $db "-user" }}
  {{- $secretKey := upper (regexReplaceAll "-db" $db "_DB_PASSWORD") }}
  {{- $password := index $secrets $secretKey }}
  {{- $_ := set $out $db (dict "user" $user "password" $password) }}
{{- end }}
{{ toYaml $out }}
{{- end }}


{{/*
Generating userlist.txt from credentials.yaml via include "pgbouncer.credentials".
Converts the YAML output back to an object and writes each entry as:
"user" "password" (with quotes).
*/}}
{{- define "pgbouncer.userlist" }}
{{- range $db, $x := include "pgbouncer.credentials" . | fromYaml }}
{{ $x.user | quote }} {{ $x.password | quote }}
{{- end }}
{{- end }}
