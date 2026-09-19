from fairy.neurofairy_chat import reply_to_user


def main() -> None:
    message = "I need to email my professor about an extension, but I feel overwhelmed."
    reply = reply_to_user(message)
    print(reply)


if __name__ == "__main__":
    main()
