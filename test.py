choice = input(f"Target group already exists. This action will delete the existing target group. Do you want to continue? (Y/n): ")
if choice.lower() == "n":
    print("Aborted by user.")