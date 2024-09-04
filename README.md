# websnap

<div>
  <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/websnap">
  <img alt="PyPI - Downloads" src="https://static.pepy.tech/badge/websnap">
  <img alt="PyPI - License" src="https://img.shields.io/pypi/l/websnap?color=%232780C1">
</div>

### Copies files retrieved from an API to a S3 bucket or a local machine.

###

---


## Installation

   ```bash
  pip install websnap
   ```


## Quickstart

### Websnap can be used as a function or as a CLI. 

<p>
<a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/overview_diagram.png" 
target="_blank">Click here to view a websnap overview diagram.</a>
</p>


###
#### Function

```python
from websnap import websnap

# Execute websnap using default arguments
websnap()

# Execute websnap passing arguments
websnap(file_logs=True, s3_uploader=True, backup_s3_count=7, early_exit=True)
```

###
#### CLI

To access CLI documentation in terminal execute: 
   ```bash
  websnap_cli --help
   ```


## Function Parameters / CLI Options

### Function Parameters
| Parameter         | Type          | Default        |
|-------------------|---------------|----------------|
| `config`          | `str`         | `"config.ini"` |
| `log_level`       | `str`         | `"INFO"`       |
| `file_logs`       | `bool`        | `False`        |
| `s3_uploader`     | `bool`        | `False`        |
| `backup_s3_count` | `int \| None` | `None`         |
| `timeout`         | `int`         | `32`           |
| `early_exit`      | `bool`        | `False`        |
| `repeat_minutes`  | `int \| None` | `None`         |
| `section_config`  | `str \| None` | `None`         |

### CLI Options
| Option              | Shortcut | Default      |
|---------------------|----------|--------------|
| `--config`          | `-c`     | `config.ini` |
| `--log_level`       | `-l`     | `INFO`       |
| `--file_logs`       | `-f`     | `False`      |
| `--s3_uploader`     | `-s`     | `False`      |
| `--backup_s3_count` | `-b`     | `None`       |
| `--timeout`         | `-t`     | `32`         |
| `--early_exit`      | `-e`     | `False`      |
| `--repeat_minutes`  | `-r`     | `None`       |
| `--section_config`  | `-n`     | `None`       |

### Description

| Function parameter /<br/> CLI option | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `config` _(str)_                     | <ul><li>Path to configuration `.ini` file</li><li>Default value expects file called `config.ini` in same directory as websnap package is being executed from</li></ul>                                                                                                                                                                                                                                                                                        |
| `log_level` _(str)_                  | <ul><li>Level to use for logging</li><li>Default value is `INFO`</li><li>Valid logging levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`</li><li><a href="https://docs.python.org/3/library/logging.html#levels" target="_blank">Click here to learn more about logging levels</a></li></ul>                                                                                                                                                      |
| `file_logs` _(bool)_                 | <ul><li>Enable rotating file logs</li></ul>                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `s3_uploader` _(bool)_               | <ul><li>Enable uploading of files to S3 bucket</li><ul>                                                                                                                                                                                                                                                                                                                                                                                                       |
| `backup_s3_count` _(int \| None)_    | <ul><li>Copy and backup file in each config section to the configured S3 bucket `backup_s3_count` times</li><li>Remove file with the oldest last modified timestamp</li><li>If omitted then files are not copied or removed</li><li>If enabled then backup files are copied and assigned the original file's name with the last modified timestamp appended</li></ul>                                                                                         |
| `timeout` _(int)_                    | <ul><li>Number of seconds to wait for response for each HTTP request before timing out</li><li>Default value is `32` seconds</li></ul>                                                                                                                                                                                                                                                                                                                        |
| `early_exit` _(bool)_                | <ul><li>Enable early program termination after error occurs</li><li>If omitted logs errors but continues program execution</li></ul>                                                                                                                                                                                                                                                                                                                          |
| `repeat_minutes` _(int \| None)_     | <ul><li>Run websnap continuously every `repeat_minutes` minutes</li><li>If omitted then websnap does not repeat</li></ul>                                                                                                                                                                                                                                                                                                                                     |
| `section_config` _(str \| None)_     | <ul><li>File or URL to obtain additional configuration sections</li><li>If omitted then default value is `None` and only config specified in `config` argument is used</li><li>Cannot be used to assign "DEFAULT" values in config</li><li>Currently only supports JSON config and can only be used if `config` argument is also a JSON file</li><li>Duplicate sections will overwrite values with the same section passed in the `config` argument</li></ul> |                                                                                                                                                                                                                                                                                                                                                                      |

## Usage: S3 Bucket

### **Copy files retrieved from an API to a S3 bucket.**

Uses the AWS SDK for Python (Boto3) to add and backup API files to a S3 bucket. 

### Examples

#### Function
```python
# The s3_uploader argument must be passed as True to copy files to a S3 bucket
# Copies files to a S3 bucket using default argument values
websnap(s3_uploader=True)

# Copies files to a S3 bucket and repeat every 1440 minutes (24 hours), 
# file logs are enabled and only 3 backup files are allowed for each config section
websnap(file_logs=True, s3_uploader=True, backup_s3_count=3, repeat_minutes=1440)
```

#### CLI
- The following CLI option **must** be used to enable websnap to upload files to a S3 bucket: `--s3_uploader`

- Copies files to a S3 bucket using default argument values:
     ```bash
      websnap_cli --s3_uploader 
     ```

- Copies files to a S3 bucket and repeat every 1440 minutes (24 hours), file 
  logs are enabled and only 3 backup files are allowed for each config section:
     ```bash
      websnap_cli --file_logs --s3_uploader --backup_s3_count 3 --repeat_minutes 1440
     ```

### Configuration

- A valid `.ini` or `.json `configuration file is **required** for both function and 
  CLI usage.
- Websnap expects the config to be `config.ini` in the same directory as websnap 
  package is being executed from.
  - However, this can be changed using the `config` function argument (or CLI 
   `--config` option).
- All keys in tables below are **mandatory**.

#### S3 Configuration Example Files

| Format  | Example Configuration File                                                                                                                                                                   |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.ini`  | <a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config_templates/s3_config_template.ini" target="_blank">src/websnap/config_templates/s3_config_template.ini</a>   |
| `.json` | <a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config_templates/s3_config_template.json" target="_blank">src/websnap/config_templates/s3_config_template.json</a> |


#### Default Configuration

Example default S3 configuration:

```
[DEFAULT]
endpoint_url=https://dreamycloud.com
aws_access_key_id=1234567abcdefg
aws_secret_access_key=hijklmn1234567
```

| Key                     | Value Description                        |
|-------------------------|------------------------------------------|
| `endpoint_url`          | URL to use for the constructed S3 client |
| `aws_secret_key_id`     | AWS access key ID                        |
| `aws_secret_access_key` | AWS secret access key                    |

#### Other Sections (one per API URL endpoint)

- _Each file retrieved from an API requires its **own config section!**_
- The section name be anything, it is suggested to have a name that relates to the 
  copied file.

Example S3 config section configuration with key prefix:

```
[resource]
url=https://www.example.com/api/resource
bucket=exampledata
key=subdirectory_resource/resource.xml
```

Example S3 config section configuration without key prefix:

```
[project]
url=https://www.example.com/api/project
bucket=exampledata
key=project.json
```


| Key      | Value Description                                       |
|----------|---------------------------------------------------------|
| `url`    | API URL endpoint that file will be retrieved from       |
| `bucket` | Bucket that file will be written in                     |
| `key`    | File name with extension, can optionally include prefix |


## Usage: Local Machine

### **Copy files retrieved from an API to a local machine.** 

### Examples

#### Function
```python
# Write files retrieved from an API to local machine using default argument values
websnap()

# Write files retrieved from an API locally and repeats every 60 minutes (1 hour), 
# file logs are enabled
websnap(file_logs=True, repeat_minutes=60)
```

#### CLI 

- Write copied files to local machine using default argument values:
     ```bash
      websnap_cli 
     ```

- Write copied files locally and repeats every 60 minutes (1 hour), file logs 
  are enabled:
     ```bash
      websnap_cli --file_logs --repeat_minutes 60
     ```

### Configuration

- A valid `.ini` or `.json` configuration file is **required** for both function and 
  CLI usage.
- Websnap expects the config to be `config.ini` in the same directory as websnap 
  package is being executed from.
  - However, this can be changed using the `config` function argument (or CLI 
   `--config` option).
- Each file that will be retrieved from an API requires its _own section_. 
- If the optional `directory` key/value pair is omitted then the file will be written in the directory that the program is executed from.


#### Configuration Example Files

| Format  | Example Configuration File                                                                                                                                                             |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.ini`  | <a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config_templates/config_template.ini" target="_blank">src/websnap/config_templates/config_template.ini</a>   |
| `.json` | <a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config_templates/config_template.json" target="_blank">src/websnap/config_templates/config_template.json</a> |


#### Sections (one per API URL endpoint)

Example local machine configuration section:

```
[project]
url=https://www.example.com/api/project
file_name=project.json
directory=projectdata
```

| Key                      | Value Description                                 |
|--------------------------|---------------------------------------------------|
| `url`                    | API URL endpoint that file will be retrieved from |
| `file_name`              | File name with extension                          |
| `directory` (_optional_) | Local directory name that file will be written in |

---

## Logs

Websnap supports optional rotating file logs.

- The following CLI option **must** be used to enable websnap to support rotating file logs: `--file_logs`
  - In function usage the following argument must be passed to support rotating file 
    logs: `file_logs=True`
- If log keys are not specified in the configuration `[DEFAULT]` section then default values in the table below will be used. 
- `log_when` expects a value used by logging module TimedRotatingFileHandler.
- <a href="https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler" target="_blank">Click here for more information about how to use TimedRotatingFileHandler.</a>
- The default values result in the file logs being rotated once every day and no removal of backup log files. 

### Configuration

Example log configuration:

```
[DEFAULT]
log_when=midnight
log_interval=1
log_backup_count=7
```

#### `[DEFAULT]` Section
| Key                | Default | Value Description                                                                                                              |
|--------------------|---------|--------------------------------------------------------------------------------------------------------------------------------|
| `log_when`         | `D`     | Specifies type of interval                                                                                                     |
| `log_interval`     | `1`     | Duration of interval (must be positive integer)                                                                                |
| `log_backup_count` | `0`     | If nonzero then at most <`log_backup_count`> files will be kept,</br>oldest log file is deleted (must be non-negative integer) |


## Minimum Download Size

Websnap supports optionally specifying the minimum download size (in kilobytes) a 
file must be to copy it from the configured API URL endpoint.

- **By default the minimum default minimum size is 0 kb.**
  - Unless specified in the configuration this means that a file of any size can be downloaded by websnap.
- Configured minimum download size must be a non-negative integer.
- If the content from the API URL endpoint is less than the configured size:
  - An error will be logged and the program continues to the next config section.
  - If the CLI option `--early_exit` (or function argument `early_exit=True`) is 
    enabled 
    then the program will terminate early.

### Configuration

Example minimum download size configuration:

```
[DEFAULT]
min_size_kb=1
```

#### `[DEFAULT]` Section
| Key           | Default | Value Description                                                 |
|---------------|---------|-------------------------------------------------------------------|
| `min_size_kb` | `0`     | Minimum download size in kilobytes (must be non-negative integer) |


## Author

Rebecca Kurup Buchholz


## Purpose

This project was developed to facilitate EnviDat resiliency and support continuous 
operation during server maintenance.

<a href="https://www.envidat.ch" target="_blank">EnviDat</a> is the environmental data 
portal of the Swiss Federal Institute for Forest, Snow and Landscape Research WSL. 


## License 

<a href="https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/LICENSE" target="_blank">MIT License</a>
