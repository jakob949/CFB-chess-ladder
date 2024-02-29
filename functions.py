def add_1_ID(s_id):
    return str(int(s_id) + 1).zfill(len(s_id))

print(add_1_ID('0999'))