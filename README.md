# websnap

#### Copies files from URLs and uploads them to a S3 bucket. 

Also supports writing files downloaded from URLs to a local machine. 


## Documentation Topics

> - [Purpose](#purpose)
> - [Installation](#installation)
> - [Quickstart](#quickstart)
> - [Function Parameters / CLI Options](#function-parameters--cli-options)
> - [Usage: S3 Bucket](#usage-s3-bucket)
> - [Usage: Local Machine](#usage-local-machine)
> - [Log Support](#log-support)
> - [Minimum Download Size](#minimum-download-size)
> - [Scheduled Pipelines Automation](#scheduled-pipelines-automation)
> - [Pre-commit Hooks](#pre-commit-hooks)
> - [Author](#author)
> - [License](#license)


## Purpose

This project was developed to facilitate EnviDat resiliency and support continuous operation during server maintenance.

[EnviDat](https://www.envidat.ch) is the environmental data portal of the Swiss Federal Institute for Forest, Snow and Landscape Research WSL. 


## Installation


   ```bash
  pip install websnap
   ```

## Quickstart

### Websnap can be used as a function or as a CLI 

#### [Click here to view a websnap overview diagram](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/overview_diagram.png?ref_type=heads)

###
#### Function

```python
import websnap

# Execute websnap using default arguments
websnap.websnap()

# Execute websnap passing arguments
websnap.websnap(file_logs=True, s3_uploader=True, backup_s3_count=7, early_exit=True)
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
| `early_exit`      | `bool`        | `False`        |
| `repeat_minutes`  | `int \| None` | `None`         |

### CLI Options
| Option              | Shortcut | Default      |
|---------------------|----------|--------------|
| `--config`          | `-c`     | `config.ini` |
| `--log_level`       | `-l`     | `INFO`       |
| `--file_logs`       | `-f`     | `False`      |
| `--s3_uploader`     | `-s`     | `False`      |
| `--backup_s3_count` | `-b`     | `None`       |
| `--early_exit`      | `-e`     | `False`      |
| `--repeat_minutes`  | `-r`     | `None`       |


### Description

| Function parameter / CLI option | Description                                                                                                                                                                                                                                                                                                               |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `config`                        | Path to configuration `.ini` file.<br/> Default value expects file called `config.ini` in same directory as websnap package is being executed from.                                                                                                                                                                       |
| `log_level`                     | Level to use for logging. Default value is `INFO`.<br/>Valid logging levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.<br/>[Click here to learn more about logging levels.](https://docs.python.org/3/library/logging.html#levels)                                                                           |
| `file_logs`                     | Enable rotating file logs.                                                                                                                                                                                                                                                                                                |
| `s3_uploader`                   | Enable uploading of files to S3 bucket.                                                                                                                                                                                                                                                                                   |
| `backup_s3_count`               | Copy and backup S3 objects in each config section <backup_s3_count> times, remove object with the oldest last modified timestamp.<br/>If omitted then objects are not copied or removed.<br/>If enabled then backup objects are copied and assigned the original object's name with the last modified timestamp appended. |
| `early_exit`                    | Enable early program termination after error occurs.<br/>If omitted logs URL processing errors but continues program execution.                                                                                                                                                                                           |
| `repeat_minutes`                | Run websnap continuously every <repeat_minutes> minutes.<br/>If omitted then websnap does not repeat.                                                                                                                                                                                                                     |
                                                                                                                                                                                                                        


## Usage: S3 Bucket

**Copy files from URLs and upload them to a S3 bucket.**

### Examples


#### Function
```python
# The s3_uploader argument must be passed as True to upload files to a S3 bucket
# Uploads files to a S3 bucket using default argument values
websnap.websnap(s3_uploader=True)

# Uploads files to a S3 bucket and repeat every 1440 minutes (24 hours), 
# file logs are enabled and only 3 backup objects are allowed for each config section
websnap.websnap(file_logs=True, s3_uploader=True, backup_s3_count=3, repeat_minutes=1440)
```

#### CLI
- The following CLI option **must** be used to enable websnap to upload files to a S3 bucket: `--s3_uploader`

- Uploads files to a S3 bucket using default argument values:
     ```bash
      websnap_cli --s3_uploader 
     ```

- Uploads files to a S3 bucket and repeat every 1440 minutes (24 hours), file logs 
  are enabled and only 3 backup objects are allowed for each config section:
     ```bash
      websnap_cli --file_logs --s3_uploader --backup_s3_count 3 --repeat_minutes 1440
     ```

### Configuration

- A valid `.ini` configuration file is **required** for both function and CLI usage.
- Websnap expects the config to be `config.ini` in the same directory as websnap 
  package is being executed from.
  - However, this can be changed using the `config` function argument (or CLI 
   `--config` option).  
- S3 config example file: [src/websnap/config_templates/s3_config_template.ini](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config/s3.config.example.ini?ref_type=heads)
- All keys in tables below are **mandatory**.

#### `[DEFAULT]` Section

Example S3 configuration `[DEFAULT]` section:

```
[DEFAULT]
endpoint_url=https://dreamycloud.com
aws_access_key_id=1234567abcdefg
aws_secret_access_key=hijklmn1234567
```

| Key                     | Value Description                            |
|-------------------------|----------------------------------------------|
| `endpoint_url`          | The URL to use for the constructed S3 client |
| `aws_secret_key_id`     | AWS access key ID                            |
| `aws_secret_access_key` | AWS secret access key                        |

#### Other Sections (one per URL)

- _Each URL file that will be downloaded requires its **own config section!**_
- The section name be anything, it is suggested to have a name that relates to the downloaded file.

Example S3 config section configuration with key prefix:

```
[resource]
url=https://www.example.com/api/resource
bucket=exampledata
key=subdirectory_resource/resource.json
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
| `url`    | URL that file will be downloaded from                   |
| `bucket` | Bucket that file will be written in                     |
| `key`    | File name with extension, can optionally include prefix |



## Usage: Local Machine

**Download files from URLs and write files to local machine.** 

### Examples

#### Function
```python
# Write downloaded files to local machine using default argument values
websnap.websnap()

# Write downloaded files locally and repeats every 60 minutes (1 hour), file logs are enabled
websnap.websnap(file_logs=True, repeat_minutes=60)
```

#### CLI 

- Write downloaded files to local machine using default argument values:
     ```bash
      websnap_cli 
     ```

- Write downloaded files locally and repeats every 60 minutes (1 hour), file logs 
  are enabled:
     ```bash
      websnap_cli --file_logs --repeat_minutes 60
     ```

### Configuration

- A valid `.ini` configuration file is **required** for both function and CLI usage.
- Websnap expects the config to be `config.ini` in the same directory as websnap 
  package is being executed from.
  - However, this can be changed using the `config` function argument (or CLI 
   `--config` option).  
- Local machine config example file: [src/websnap/config_templates/config_template.ini](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/src/websnap/config/config.example.ini?ref_type=heads)
- Each URL file that will be downloaded requires its _own section_. 
- If the optional `directory` key/value pair is omitted then the file will be written in the directory that the program is executed from.

Example local machine configuration section:

```
[project]
url=https://www.example.com/api/project
file_name=project.json
directory=projectdata
```

#### Sections (one per URL)

| Key                      | Value Description                           |
|--------------------------|---------------------------------------------|
| `url`                    | URL that file will be downloaded from       |
| `file_name`              | File name with extension                    |
| `directory` (_optional_) | Directory name that file will be written in |


## Log Support

Websnap supports optional rotating file logs.

- The following CLI option **must** be used to enable websnap to support rotating file logs: `--file_logs`
  - In function usage the following argument must be passed to support rotating file 
    logs: `file_logs=True`
- If log keys are not specified in the configuration `[DEFAULT]` section then default values in the table below will be used. 
- `log_when` expects a value used by logging module TimedRotatingFileHandler.
- For more details about how to use TimedRotatingFileHandler please [click here](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
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
| Key                | Default | Value Description                                                                                                          |
|--------------------|---------|----------------------------------------------------------------------------------------------------------------------------|
| `log_when`         | `D`     | Specifies type of interval                                                                                                 |
| `log_interval`     | `1`     | Duration of interval (must be positive integer)                                                                            |
| `log_backup_count` | `0`     | If nonzero then at most <`log_backup_count`> files will be kept, oldest log file is deleted (must be non-negative integer) |


## Minimum Download Size

Websnap supports optionally specifying the minimum download size (in kilobytes) a file must be to download it from the configured URL.

- **By default the minimum default minimum size is 0 kb.**
  - Unless specified in the configuration this means that a file of any size can be downloaded by websnap.
- Configured minimum download size must be a non-negative integer.
- If the content from the URL is less than the configured size:
  - An error will be logged and the program continues to the next config section.
  - If the CLI option `--early_exit` (or function argument `early_exit=True)`is enabled 
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


## Scheduled Pipelines Automation

A CI/CD pipeline is currently used to automate execution of websnap using a GitLab pipeline schedule. 

#### Pipeline script specifications:
- For details see `.gitlab-ci.yml`
- Uploads objects to a S3 bucket
- Backs up S3 objects
- Early exit is enabled, this causes pipeline failure if an error occurs

#### Pipeline required CI/CD variables:
- CONFIG_INI - text with required S3 config values, for example see 
  `src/websnap/config_templates/s3_config_template.ini`
- BACKUP_S3_COUNT - number of S3 objects to back up for each configured URL


## Pre-commit Hooks

Pre-commit hooks ensure that the application uses stylistic conventions before code changes can be commited.

Pre-commit hooks are specified in `.pre-commit-config.yaml`.

To install pre-commit hooks for use during development execute:
 ```bash
  pdm run pre-commit install
  ```

To run pre-commit hooks manually on all files execute:
  ```bash
  pre-commit run --all-files
  ```

## Author
[Rebecca Kurup Buchholz](https://www.linkedin.com/in/rebeccakurupbuchholz/), Swiss Federal Institute for Forest, Snow and Landscape Research WSL 


## License

[MIT License](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/LICENSE?ref_type=heads)

