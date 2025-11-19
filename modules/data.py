
def get_schools():
    with open('data/school_names.txt', 'r', encoding='utf-8') as f:
        school_names = [line.strip() for line in f.readlines()]
    return school_names