from collections import UserDict
from datetime import datetime, date, timedelta
import pickle
from abc import ABC, abstractmethod


class UserInterface(ABC):

    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def get_input(self, prompt):
        pass

    @abstractmethod
    def show_contact(self, name, phones, birthday=None):
        pass

    @abstractmethod
    def show_all_contacts(self, contacts):
        pass

    @abstractmethod
    def show_upcoming_birthdays(self, upcoming_birthdays):
        pass


class ConsoleInterface(UserInterface):

    def show_message(self, message):
        print(message)

    def get_input(self, prompt):
        return input(prompt)

    def show_contact(self, name, phones, birthday=None):
        phones_str = ", ".join(phones)
        birthday_str = f", birthday: {birthday}" if birthday else ""
        print(f"{name}: {phones_str}{birthday_str}")

    def show_all_contacts(self, contacts):
        print("Name   Phone")
        for name, record in contacts.items():
            phones_str = ", ".join(p.value for p in record.phones)
            print(f"{name}: {phones_str}")

    def show_upcoming_birthdays(self, upcoming_birthdays):
        if not upcoming_birthdays:
            print("No upcoming birthdays this week.")
        else:
            print("Upcoming birthdays this week:")
            for record in upcoming_birthdays:
                print(f"{record['name']} ({record['congratulation_date']})")


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def input_error(func):
    def wrapper(*args):
        try:
            return func(*args)
        except IndexError:
            print("Not enough arguments. Please provide all required arguments.")
        except KeyError:
            print("Contact not found.")
        except ValueError as e:
            print(e)

    return wrapper


def input_error_change(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            if len(args[0]) == 2:
                return "Give me new phone please."
            if len(args[0]) == 1:
                return "Give me old and new phone please."
            return "Give me name and tow phones please."
        except KeyError:
            return "Contact not find. Give me another name please."
        except AssertionError as e:
            return e

    return inner


def input_error_add(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            if len(args[0]) == 1:
                return "Give me phone please."
            return "Give me name and phone please."
        except AssertionError as e:
            return e

    return inner


def input_error_find(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name please."
        except KeyError:
            return "Contact name not found."
        except IndexError:
            return "Give me name please."
        except AssertionError as e:
            return e

    return inner


@input_error_add
def add_contact(args, book):
    name, phone = args
    if book.find(name):
        return book.update(name, phone=phone)
    else:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."


@input_error_find
def find_contact(args, book):
    name, *_ = args
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(p.value for p in record.phones)}"
    else:
        return f"Contact {name} not found."


@input_error_change
def change_contact(args, book):
    name, phone_old, phone_new = args
    record = book.find(name)
    if record:
        try:
            record.edit_phone(phone_old, phone_new)
            return f"Phone number {phone_old} change to {phone_new}."
        except ValueError as e:
            return str(e)
    else:
        return f"Contact {name} not found."


@input_error
def add_birthday(args, book):
    name, birthday, *_ = args
    record = book.find(name)
    if record:
        try:
            record.add_birthday(birthday)
            return f"Birthday {birthday} added for {name}."
        except ValueError as e:
            return str(e)
    else:
        return f"Contact {name} not found."


@input_error
def show_birthday(args, book):
    name, *_ = args
    record = book.find(name)
    if record:
        if record.birthday:
            return f"{name}'s birthday: {record.birthday.value}"
        else:
            return f"No birthday set for {name}."
    else:
        return f"Contact {name} not found."


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        print("No upcoming birthdays this week.")
    else:
        print("Upcoming birthdays this week:")
        for record in upcoming:
            print(f"{record['name']} ({record['congratulation_date']})")


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def string_to_date(date_string):
    return datetime.strptime(date_string, "%Y.%m.%d").date()


def date_to_string(date):
    return date.strftime("%Y.%m.%d")


def prepare_user_list(user_data):
    prepared_list = []
    for user in user_data:
        prepared_list.append({"name": user["name"], "birthday": string_to_date(user["birthday"])})
    return prepared_list


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        assert len(value) > 0, f"Name is required"
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        assert value.isdigit() and len(value) == 10, f"Phone must have 10 digit character"
        super().__init__(value)


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def edit_phone(self, phone_old, phone_new):
        phone = next(filter(lambda p: p.value == phone_old, self.phones), None)
        self.phones.remove(phone)
        self.add_phone(phone_new)

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p

    def remove_phone(self, phone):
        matching_phone = next((p for p in self.phones if p.value == phone), None)
        if matching_phone is not None:
            self.phones.remove(matching_phone)


class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class AddressBook(UserDict):

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def update(self, name, phone=None, birthday=None):
        record = self.find(name)
        if record:
            if phone:
                record.add_phone(phone)
            if birthday:
                record.add_birthday(birthday)
            return f"Contact {name} updated."
        else:
            return f"Contact {name} not found."

    def delete(self, name):
        self.data.pop(name, None)

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = record.birthday.value.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= days:
                    adjusted_birthday = adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = date_to_string(adjusted_birthday)
                    upcoming_birthdays.append(
                        {"name": record.name.value, "congratulation_date": congratulation_date_str})

        return upcoming_birthdays


def main():
    ui = ConsoleInterface()
    ui.show_message("Welcome to the assistant bot!")
    book = load_data()

    while True:
        command, *args = parse_input(ui.get_input("Enter a command: "))

        if command in ["close", "exit"]:
            ui.show_message("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            ui.show_message("How can I help you?")
        elif command == "add":
            ui.show_message(add_contact(args, book))
        elif command == "change":
            ui.show_message(change_contact(args, book))
        elif command == "phone":
            ui.show_message(find_contact(args, book))
        elif command == "all":
            ui.show_all_contacts(book.data)
        elif command == "add-birthday":
            ui.show_message(add_birthday(args, book))
        elif command == "show-birthday":
            ui.show_message(show_birthday(args, book))
        elif command == "birthdays":
            upcoming = book.get_upcoming_birthdays()
            ui.show_upcoming_birthdays(upcoming)
        else:
            ui.show_message("Invalid command.")


if __name__ == "__main__":
    main()
