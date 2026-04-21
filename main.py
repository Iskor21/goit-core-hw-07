from collections import UserDict
from datetime import datetime, date, timedelta

# для запису полів
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value: str):
        super().__init__(value)

# валідація номера
class Phone(Field):
    def __init__(self, value: str):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone must contain 10 number.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            if isinstance(value, str): # Додайте перевірку коректності даних
                value = datetime.strptime(value, "%d.%m.%Y").date() # та перетворіть рядок на об'єкт datetime
            elif isinstance(value, datetime):
                value = value.date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

#Додавання телефонів. Видалення телефонів. Редагування телефонів. Пошук телефону.
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def add_birthday(self, birthday: Birthday):
        self.birthday = birthday

    def remove_phone(self, number):
        found = self.find_phone(number)
        if found:
            self.phones.remove(found)
        else:
            return f"Phone {phone} not found."

    def find_phone(self, number):
        for phone in self.phones:
            if  phone.value == number:
                return phone
        return None

    def edit_phone(self, old_number: str, new_number: str):
        found = self.find_phone(old_number)
        if found:
            try:
                self.add_phone(new_number)   # перевірка валідності
                self.remove_phone(old_number)
                return new_number
            except ValueError as e:
                raise ValueError(f"New phone {new_number} not valid: {e}")
        else:
            raise ValueError(f"Phone {old_number} does not found.")

    def __str__(self):
        phones = "; ".join(str(p) for p in self.phones) if self.phones else "-"
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "-"
        return f"{self.name.value}, phones: {phones}, birthday: {birthday}"


#Додавання записів. Пошук записів за іменем. Видалення записів за іменем.
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name: Record):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                # беремо саме datetime.date з Birthday.value
                birthday_this_year = record.birthday.value.replace(year=today.year)
                delta_days = (birthday_this_year - today).days

                if 0 < delta_days <= days:
                    if birthday_this_year.weekday() < 5:
                        upcoming_birthdays.append({
                            "name": record.name.value,
                            "congratulation_date": birthday_this_year.strftime("%d.%m.%Y")
                        })
                    else:
                        weekday = 0  # понеділок
                        days_ahead = weekday - birthday_this_year.weekday()
                        if days_ahead <= 0:
                            days_ahead += 7
                        birthday_this_year = birthday_this_year + timedelta(days=days_ahead)
                        upcoming_birthdays.append({
                            "name": record.name.value,
                            "congratulation_date": birthday_this_year.strftime("%d.%m.%Y")
                        })
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def parse_input(user_input):
    parts = user_input.split()
    if not parts:  # якщо рядок порожній
        return None, []
    cmd, *args = parts
    cmd = cmd.strip().lower()
    return cmd, args


def input_error(func):
    def inner(*args, **kwargs):
        try:
            if not args and not kwargs:
                return "No command entered. Please enter a command."
            contacts = None
            if "contacts" in kwargs and isinstance(kwargs["contacts"], dict):
                contacts = kwargs["contacts"]
            else:
                if len(args) >= 2 and isinstance(args[1], dict):
                    contacts = args[1]
                else:
                    for a in args:
                        if isinstance(a, dict):
                            contacts = a
                            break
            data = None
            if args:
                first = args[0]
                if isinstance(first, (list, tuple)):
                    data = first
                elif isinstance(first, str):
                    data = first.split()
            if contacts and data and len(data) >= 2:
                name, phone = data[0], data[1]
                for existing_name, existing_phone in contacts.items():
                    if phone == existing_phone and existing_name != name:
                        return f"This phone number belongs to {existing_name}."
                if func.__name__ == "add_contact" and name in contacts:
                    return f"Contact {name} already exists. If you want to change number please use 'change' command."
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact does not exist."
        except IndexError:
            return "Enter name and phone correctly."
        except TypeError:
            return "No command entered. Please enter a command."
    return inner


@input_error
def add_contact(args, book: AddressBook, filename="AddressBook.txt"):
    name = args[0]
    phone = args[1] if len(args) > 1 else None

    record = book.find(name)
    if record is None:
        # створюємо новий контакт
        record = Record(name)
        if phone:
            record.add_phone(phone)
        book.add_record(record)   # додаємо у книгу навіть якщо телефону немає
        message = "Contact added."
    else:
        # додаємо телефон до існуючого контакту
        if phone:
            try:
                record.add_phone(phone)
                message = "Phone added."
            except ValueError as e:
                return f"Invalid phone: {e}"
        else:
            message = "Contact already exists. No phone provided."

    # збереження у файл
    with open(filename, "w", encoding="utf-8") as f:
        for rec in book.data.values():
            phones = ";".join(p.value for p in rec.phones) if rec.phones else ""
            f.write(f"{rec.name.value},{phones}\n")

    return message





@input_error
def change_contact(args, book: AddressBook, filename="AddressBook.txt"):
    name, old_phone, new_phone = args

    record = book.find(name)
    if not record:
        raise KeyError(name)

    try:
        record.edit_phone(old_phone, new_phone)
    except ValueError as e:
        return str(e)

    # після зміни телефону зберігаємо всю книгу у файл
    with open(filename, "w", encoding="utf-8") as f:
        for rec in book.data.values():
            phones = ";".join(p.value for p in rec.phones) if rec.phones else ""
            birthday_str = rec.birthday.value.strftime("%d.%m.%Y") if rec.birthday else ""
            f.write(f"{rec.name.value},{phones},{birthday_str}\n")

    return f"Phone for {name} changed from {old_phone} to {new_phone}."


def load_contacts(filename="AddressBook.txt"):
    book = AddressBook()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.split(",")]
                if not parts or not parts[0]:
                    continue

                name = parts[0]
                phones = parts[1].split(";") if len(parts) > 1 and parts[1] else []
                birthday = parts[2] if len(parts) > 2 and parts[2] else None

                record = Record(name)

                # додаємо телефони
                for phone in phones:
                    phone = phone.strip()
                    if phone:
                        try:
                            record.add_phone(phone)
                        except ValueError:
                            pass

                # додаємо день народження
                if birthday and birthday.strip():
                    try:
                        record.add_birthday(Birthday(birthday))
                    except ValueError:
                        pass

                book.add_record(record)
    except FileNotFoundError:
        pass
    return book



@input_error
def phone_contact(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if not record:
        return f"Contact {name} not found."

    phones = "; ".join(p.value for p in record.phones) if record.phones else "-"
    return f"{name}: {phones}"


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        return "Enter name and birthday in format DD.MM.YYYY"
    name, birthday = args[0], args[1]
    record = book.find(name)
    if not record:
        return "Contact not found. Use command add firstly"
    try:
        record.add_birthday(Birthday(birthday))
        return "Birthday added."
    except ValueError as e:
        return str(e)

@input_error
def show_birthday(args, book: AddressBook):
    if not args or len(args) < 1:
        return "Enter name for the command 'show-birthday'."

    name = args[0]
    record = book.find(name)
    if not record:
        raise KeyError(name)

    if record.birthday:
        return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"
    else:
        return f"{name} has no birthday set."

def birthdays(book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    result = []
    for item in upcoming:
        result.append(f"{item['name']}'s congratulation date on {item['congratulation_date']}")
    return "\n".join(result)

def all_contacts(book: AddressBook):
    return [str(record) for record in book.values()]

def save_contacts(book: AddressBook, filename="AddressBook.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for rec in book.data.values():
            phones = ";".join(p.value for p in rec.phones) if rec.phones else ""
            birthday = rec.birthday.value.strftime("%d.%m.%Y") if rec.birthday else ""
            f.write(f"{rec.name.value},{phones},{birthday}\n")


def main():
    book = load_contacts()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command is None:  # порожній рядок
            print("No command entered. Please enter a command.")
            continue

        if command in ["close", "exit"]:
            save_contacts(book) # збереження всіх записів перед виходом
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(phone_contact(args, book))
        elif command == "all":
            print("\n".join(all_contacts(book)))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()