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

- **-config** - Path to configuration `.ini` file. Default expects `config.ini` at `./src/websnap/config/config.ini`.
- **log_level** - Level to use for logging. 


## Usage: S3 Bucket

Download files from URLs and upload them to S3 bucket.

### Commands

TODO document S3 commands here.

### Configuration

TODO document S3 configuration here
TODO document config citing example.ini files


## Usage: Local Machine

### Commands

TODO document local machine commands here

### Configuration

TODO document local machine configuration here

TODO document config citing example.ini files


## Log Support

TODO document configuring file logs.


## Scheduled Pipelines

TODO document


## Pre-commit Hooks

TODO test pre-commit hook. 

- To run the pre-commit hooks manually open app in terminal and execute: `pre-commit run --all-files`
- These hooks ensure that the application uses standard stylistic conventions
- To view or alter the pre-commit hooks see: `.pre-commit-config.yaml`


## Author
[Rebecca Kurup Buchholz](https://www.linkedin.com/in/rebeccakurupbuchholz/), Swiss Federal Institute for Forest, Snow and Landscape Research WSL 


## License

[MIT License](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/LICENSE?ref_type=heads)

