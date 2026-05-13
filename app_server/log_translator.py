from app_server import google_credentials


def do_translate():
    from google.cloud import translate_v2 as translate
    full_text = ""
    with open(r"D:\Sources\_AIASS\qa_remix.txt", "r", encoding="utf-8") as f:
        full_text = f.read()
    print("got to create client")
    translate_client = translate.Client(credentials=google_credentials)
    print("got to translate", full_text[:200])
    translate_result = translate_client.translate(full_text[:200], target_language="ch", source_language="my")
    with open(r"D:\Sources\_AIASS\qa_remix_ch.txt", "w", encoding="utf-8") as f:
        f.write(translate_result["translatedText"])


if __name__ == '__main__':
    do_translate()

