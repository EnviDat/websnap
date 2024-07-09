# websnap

#### CLI that downloads files from URLs and upload them to a S3 bucket. 

Also supports writing downloaded files to local machine. 

[EnviDat](https://www.envidat.ch) is the environmental data portal of the Swiss Federal Institute for Forest, Snow and Landscape Research WSL.

TODO include diagram


## Documentation Topics

> - [Installation](#installation)
> - [CLI Options](#cli-options)
> - [Usage: S3 Bucket](#usage-s3-bucket)
> - [Usage: Local Machine](#usage-local-machine)
> - [Log Support](#log-support)
> - [Scheduled Pipelines](#scheduled-pipelines)
> - [Pre-commit Hooks](#pre-commit-hooks)
> - [Author](#author)
> - [License](#license)


## Installation

Project uses PDM package and dependency manager. 

Clone repository and then execute:

   ```bash
  pip install pdm
  pdm install
   ```

Project metadata and dependencies are listed in `pyproject.toml`

[Click here for PDM official documentation.](https://pdm-project.org/en/latest/)


## CLI Options

To access CLI options documentation in terminal execute: 
   ```bash
  pdm run websnap-cli --help
   ```

###
| Option              | Shortcut  | Default                           |
|---------------------|-----------|-----------------------------------|
| `--config`          | `-c`      | `./src/websnap/config/config.ini` |
| `--log_level`       | `-l`      | `INFO`                            |
| `--file_logs`       | `-f`      | `False`                           |
| `--s3_uploader`     | `-s`      | `False`                           |
| `--backup_s3_count` | `-b`      | `None`                            |
| `--early_exit`      | `-e`      | `False`                           |
| `--repeat`          | `-r`      | `None`                            |

- **config** - Path to configuration `.ini` file. 
  - Default value expects `config.ini` at `./src/websnap/config/config.ini`.

- **log_level** - Level to use for logging. Default value is `INFO`. 
  - Valid logging levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
  - [Click here to learn more about logging levels.](https://docs.python.org/3/library/logging.html#levels)

- **file_logs** - Enable rotating file logs. 

- **s3_uploader** - Enable uploading of files to S3 bucket. 

- **backup_s3_count** - Copy and backup S3 objects in each config section 
                        <backup_s3_count> times, remove object with the oldest last 
                        modified timestamp. 
  - If omitted then objects are not copied or removed.

- **early_exit** - Enable early program termination after error occurs. 
  - If omitted logs URL processing errors but continues program execution.

- **repeat** - Run websnap continuously every <repeat> minutes. 
  - If omitted then websnap does not repeat.



## Usage: S3 Bucket

**Download files from URLs and upload them to S3 bucket.**

### Example Commands

- The following CLI option **must** be used to enable websnap to upload files to a S3 bucket: `--s3_uploader`


- Uploads files to a S3 bucket using default argument values:
     ```bash
      pdm run websnap-cli --s3_uploader 
     ```

- Uploads files to a S3 bucket and repeat every 1440 minutes (24 hours), file logs are enabled and only 3 backup objects are allowed for each config section:
     ```bash
      pdm run websnap-cli --file_logs --s3_uploader --backup_s3_count 3 --repeat 1440
     ```

### Configuration

- A valid `.ini` configuration file is required. 
- The CLI expects the config to be `config.ini` at `./src/websnap/config/config.ini`.
  - However, this can be changed using the CLI `--config` option.  
- S3 config example file: `src/websnap/config/s3.config.example.ini`
- All keys in tables below are **mandatory**.
- Each URL file that will be downloaded requires its _own section_. 

Example S3 configuration:

```
[DEFAULT]
endpoint_url=https://dreamycloud.com
aws_access_key_id=1234567abcdefg
aws_secret_access_key=hijklmn1234567

[resource]
url=https://www.example.com/api/resource
bucket=exampledata
key=subdirectory_resource/resource.json
```

#### `[DEFAULT]` Section

| Key                     | Value Description                            |
|-------------------------|----------------------------------------------|
| `endpoint_url`          | The URL to use for the constructed S3 client |
| `aws_secret_key_id`     | AWS access key ID                            |
| `aws_secret_access_key` | AWS secret access key                        |

#### Other Sections (one per URL)

| Key      | Value Description                                       |
|----------|---------------------------------------------------------|
| `url`    | URL that file will be downloaded from                   |
| `bucket` | Bucket that file will be written in                     |
| `key`    | File name with extension, can optionally include prefix |



## Usage: Local Machine

**Download files from URLs and write files to local machine.** 

### Example Commands

- Write downloaded files to local machine using default argument values:
     ```bash
      pdm run websnap-cli 
     ```

- Write downloaded files locally and repeats every 60 minutes (1 hour), file logs are enabled:
     ```bash
      pdm run websnap-cli --file_logs --repeat 60
     ```

### Configuration

- A valid `.ini` configuration file is required. 
- The CLI expects the config to be `config.ini` at `./src/websnap/config/config.ini`.
  - However, this can be changed using the CLI `--config` option.  
- Local machine config example file: `src/websnap/config/config.example.ini`
- Each URL file that will be downloaded requires its _own section_. 

Example local machine configuration section:

```
[project]
url=https://www.example.com/api/project
file_name=project.json
directory=projectdata
```

#### Sections (one per URL)

| Key                    | Value Description                           |
|------------------------|---------------------------------------------|
| `url`                  | URL that file will be downloaded from       |
| `file_name`            | File name with extension                    |
| `directory` (optional) | Directory name that file will be written in |


## Log Support

Websnap offers support for rotating file logs.

- The following CLI option **must** be used to enable websnap to support rotating file logs: `--file_logs`
- If log keys are not specified in the configuration `[DEFAULT]` section then default values in the table below will be used. 
- `log_when` expects a value used by logging module TimedRotatingFileHandler.
- For more details about how to use TimedRotatingFileHandler please [click here](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
- The default values result in the file logs being rotated once every day and no removal of backup log files. 

### Configuration

#### `[DEFAULT]` Section
| Key                | Default | Value Description                                                                                                 |
|--------------------|---------|-------------------------------------------------------------------------------------------------------------------|
| `log_when`         | `D`     | Specifies type of interval                                                                                        |
| `log_interval`     | `1`     | Duration of interval (positive integer)                                                                           |
| `log_backup_count` | `0`     | If nonzero then at most <log_backup_count> files will be kept, oldest log file is deleted. (non-negative integer) |


## Minimum Download Size

TODO document


## Scheduled Pipelines

TODO document


## Pre-commit Hooks

Pre-commit hooks ensure that the application uses stylistic conventions before code changes can be commited.

Pre-commit hooks are specified in `.pre-commit-config.yaml`

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

