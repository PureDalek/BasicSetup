import logging
import os

def configure_logger(logger_name, log_file_path, log_level=logging.INFO):
    """
    Configures a logger with the specified settings.

    Parameters:
    - logger_name (str): The name for the logger instance.
    - log_file_path (str): The file path to save the log output.
    - log_level (int): The log level. Default is logging.INFO.

    Returns:
    - logging.Logger: Configured logger instance.
    """

    # Create a logger object
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Create file and console handlers
    file_handler = logging.FileHandler(log_file_path)
    console_handler = logging.StreamHandler()

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def main():
    """
    Main function to demonstrate logger usage.
    """

    # Configure logger
    log_file_path = os.path.join(os.getcwd(), 'application.log')
    logger = configure_logger('my_application', log_file_path)

    # Log messages at different levels
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')

if __name__ == '__main__':
    main()
