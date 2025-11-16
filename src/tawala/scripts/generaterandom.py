from django.core.management.utils import get_random_secret_key
from termcolor import colored

if __name__ == "__main__":
    print(colored(get_random_secret_key(), "green", attrs=["bold"]))
