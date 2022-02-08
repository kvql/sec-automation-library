
import logging
import sec_automation.configmanager as cm


# Set proxy variables
cm.load_config('proxy')

# Create loggers
log_level = cm.load_config('log_level')
functions.create_logger("secops_automation", log_level)

if __name__ == '__main__':
  # script code .....
    