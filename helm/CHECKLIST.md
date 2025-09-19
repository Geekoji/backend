# A checklist for Helm `values.yaml` or `secrets.yaml` to avoid catching nasty conversions 👇

---
## 📌 Which values should always be wrapped in quotation marks

> ### **Long numbers (more than 9-10 digits)**
>   ```yaml
>   FACEBOOK_WEB_CLIENT_ID: "1280574866796547"
>   ```
> Otherwise, YAML will turn it into a float and give you an exponent.

> ### **Boolean-like strings**
>   ```yaml
>   ENABLE_SSL: "true"
>   DEBUG: "false"
>   ```
> Otherwise, they are interpreted as bool and may change type unexpectedly.

> ### **Strings that look like numbers but aren't numbers** (e.g., with leading zeros, versions)
>   ```yaml
>   ZIP_CODE: "01234"
>   VERSION: "1.0.0"
>   ```
> Without the quotes, `01234` can become an octal number, and `1.0.0` invalid YAML altogether.

> ### **UUID, hashes, tokens**
>   ```yaml
>   SECRET_KEY: "f7a2cdb5-9e1c-4d0c-b62b-f44e57e6c9e2"
>   JWT_SECRET: "abc123=="
>   ```

> ### **IP addresses and domains**
>   ```yaml
>   HOST: "192.168.0.1"
>   DOMAIN: "example.com"
>   ```
>   Otherwise, YAML may perceive it as a number with a dot.

> ### **Values with `yes/no`, `on/off`**
>   ```yaml
>   FEATURE_FLAG: "on"
>   ENABLE_SSL: "yes"
>   ```
>   Without the quotation marks, YAML is a bool.

---

## 📌 When it's okay without the quotation marks

> ### **Small numbers that are real numbers**
>  ```yaml
>  REPLICAS: 3
>  TIMEOUT: 30
>  ```

> ### **Booleans that are really boolean**
>  ```yaml
>  ENABLE_METRICS: true
>  ```

---

## ⚡ General principle:

> * Anything that can be ambiguous → **always a quoted string**.
> * Anything that is unambiguously a number or bool → can be left out.
