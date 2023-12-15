import re
import sqlite3
import matplotlib.pyplot as plt

def extract_printable_ascii(data):
    regex_patterns = {
        'letters': r'([A-Za-z]+)',
        'digits': r'(\d+)',
        'special_characters': r'([!@#$%^&*()_+=\[\]{}|\\:;"<>,.?/~`-]+)',
    }
    results = {category: [] for category in regex_patterns}

    context_window = 100

    for category, regex_pattern in regex_patterns.items():
        matches = re.finditer(regex_pattern, data)
        for match in matches:
            offset_start = match.start()
            offset_end = match.end()
            value = match.group(1)
            before = data[max(0, offset_start - context_window):offset_start]
            after = data[offset_end:min(offset_end + context_window, len(data))]
            result_info = {
                'offset_start': hex(offset_start),
                'offset_end': hex(offset_end),
                'value': value,
                'context': f'{before} <{value}> {after}'
            }
            results[category].append(result_info)

    return results

def create_database():
    conn = sqlite3.connect('categorized_data.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorized_data (
            category TEXT,
            offset_start TEXT,
            offset_end TEXT,
            value TEXT,
            context TEXT
        )
    ''')

    conn.commit()
    conn.close()

def insert_into_database(data):
    conn = sqlite3.connect('categorized_data.db')
    cursor = conn.cursor()

    for category, matches in data.items():
        for match in matches:
            cursor.execute('''
                INSERT INTO categorized_data (category, offset_start, offset_end, value, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (category, match['offset_start'], match['offset_end'], match['value'], match['context']))

    conn.commit()
    conn.close()

def search_database(search_term):
    try:
        conn = sqlite3.connect('categorized_data.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM categorized_data')
        all_data = cursor.fetchall()

        conn.close()

        if all_data:
            search_result = []

            for row in all_data:
                matches = re.finditer(search_term, row[3])
                for match in matches:
                    result_info = {
                        'offset_start': hex(match.start()),
                        'offset_end': hex(match.end()),
                        'value': match.group(),
                        'context': row[4]
                    }
                    search_result.append(result_info)

            return search_result

        else:
            return None

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

def visualize_data(data):
    categories = list(data.keys())
    counts = [len(data[category]) for category in categories]

    plt.figure(figsize=(8, 6))
    plt.bar(categories, counts)
    plt.xlabel('Categories')
    plt.ylabel('Count')
    plt.title('Categorized Data Visualization')
    plt.show()

def read_ascii_characters_from_file(filename):
    try:
        with open(filename, 'r') as file:
            data = file.read()
        return data
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return None

if __name__ == "__main__":
    extracted_data = None  # Initialize outside the loop

    while True:
        print("\nOptions:")
        print("1. Enter new data")
        print("2. Read ASCII characters from a file")
        print("3. Search for data")
        print("4. Visualize categorized data")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            data_blob = input("Enter the data to be categorized: ")
            if data_blob:
                extracted_data = extract_printable_ascii(data_blob)
                create_database()
                insert_into_database(extracted_data)
                print("Data has been categorized and stored.")
            else:
                print("No data entered.")
        elif choice == "2":
            filename = input("Enter the filename to read ASCII characters from: ")
            if filename:
                data_blob = read_ascii_characters_from_file(filename)
                if data_blob is not None:
                    extracted_data = extract_printable_ascii(data_blob)
                    create_database()
                    insert_into_database(extracted_data)
                    print("Data has been read, categorized, and stored.")
                else:
                    print("Error reading data from the file.")
            else:
                print("No filename entered.")
        elif choice == "3":
            search_term = input("Enter the search term: ")
            if search_term:
                search_result = search_database(search_term)
                if search_result is not None:
                    if search_result:
                        for idx, result_info in enumerate(search_result):
                            offset_start = result_info['offset_start']
                            offset_end = result_info['offset_end']
                            value = result_info['value']
                            context = result_info['context']
                            print(f"Result {idx + 1}: [{offset_start}-{offset_end}] <{value}>")
                            print(f"Context: {context}\n")
                    else:
                        print("No matching data found.")
                else:
                    print("Error occurred during the search.")
            else:
                print("No search term entered.")
        elif choice == "4":
            if extracted_data is not None:
                visualize_data(extracted_data)
            else:
                print("Data has not been categorized yet. Please choose option 1 or 2 first.")
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please choose a valid option.")
