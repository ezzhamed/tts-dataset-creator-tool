import os
import shutil


class SplitDataset:


    def __init__(self, folder_path, new_folder_path, chunk_size):
        self.folder_path = folder_path
        self.new_folder_path = new_folder_path
        self.chunk_size = chunk_size


    def split_into_chunks(self):
        audios = sorted(os.listdir(self.folder_path))

        audios_chunks = [audios[i:i+self.chunk_size] for i in range(0, len(audios), self.chunk_size)]

        total_audio_files = sum(len(chunk) for chunk in audios_chunks)
        print(f"Total number of audio files: {total_audio_files}")

        for i, chunk in enumerate(audios_chunks):
            new_chunk_path = self.new_folder_path + f'_{i+1}'
            os.makedirs(new_chunk_path, exist_ok=True)
            for audio in chunk:
                current_audio_path = os.path.join(self.folder_path, audio)
                new_audio_path = os.path.join(new_chunk_path, audio)
                shutil.move(current_audio_path, new_audio_path)


class MergeDataset:

    def __init__(self, folders_path, new_folder_path):
        self.folders_path = folders_path
        self.new_folder_path = new_folder_path
    

    def merge_folders(self):
        folders = os.listdir(self.folders_path)

        for folder in folders:
            if 'test' not in folder:
                continue
            for audio in os.listdir(folder):
                current_audio_path = os.path.join(folder, audio)
                new_audio_path = os.path.join(self.new_folder_path, audio)
                shutil.move(current_audio_path, new_audio_path)


if __name__ == '__main__':
    # split = SplitDataset('./test', './test_folder', 10)
    # split.split_into_chunks()
    merge_dataset = MergeDataset('./', './audios/splitted_audios')
    merge_dataset.merge_folders()