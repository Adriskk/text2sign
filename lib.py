def get_merged_video_filename(sentence: str) -> str:
    return '_'.join(sentence.split(' '))


def remove_brackets(title: str) -> str:
	start_index = title.find('(')
	if start_index != -1:
		return title[:start_index].strip()
	return title.strip()