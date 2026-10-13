#!/bin/bash
# reel-kit dans une session cloud Claude Code : kit, rendu HyperFrames, transcription WhisperX.
# A coller dans les reglages de l'environnement > Setup script.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/node22/bin:$PATH" GIT_LFS_SKIP_SMUDGE=1

# Le kit
[ -d ~/reel-kit/.git ] || git clone -q --depth 1 https://github.com/antoineblc99/reel-kit ~/reel-kit

# Rendu : le Chrome deja installe dans le conteneur
B=$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell | tail -1)
grep -q HYPERFRAMES_BROWSER_PATH ~/.bashrc 2>/dev/null || echo "export HYPERFRAMES_BROWSER_PATH=$B" >> ~/.bashrc
npx --yes hyperframes@0.8.42 --version >/dev/null

# Transcription : WhisperX (~/.reel-kit/venv)
bash ~/reel-kit/scripts/setup-whisperx.sh

# Silero (detection de la voix) par git : les telechargements web de GitHub sont bloques ici
[ -d ~/.reel-kit/silero-vad ] || git clone -q --depth 1 https://github.com/snakers4/silero-vad ~/.reel-kit/silero-vad
~/.reel-kit/venv/bin/python - <<'EOF'
import os
import whisperx.vads.silero as m
path = m.__file__
src = open(path).read()
old = """        self.vad_pipeline, vad_utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                      model='silero_vad',
                                                      force_reload=False,
                                                      onnx=False,
                                                      trust_repo=True)"""
new = """        import os
        local = os.path.expanduser('~/.reel-kit/silero-vad')
        hub = dict(repo_or_dir=local, source='local') if os.path.isdir(local) else dict(repo_or_dir='snakers4/silero-vad', trust_repo=True)
        self.vad_pipeline, vad_utils = torch.hub.load(model='silero_vad', force_reload=False, onnx=False, **hub)"""
if "reel-kit/silero-vad" not in src:
    assert src.count(old) == 1, f"unexpected content in {path}"
    # nouveau fichier puis rename : uv partage ce fichier avec son cache (hardlink)
    open(path + ".tmp", "w").write(src.replace(old, new))
    os.replace(path + ".tmp", path)
print("silero local ok")
EOF

# Decoupage des phrases pour l'alignement WhisperX (NLTK refuse de telecharger a travers le proxy du conteneur)
if [ ! -d ~/nltk_data/tokenizers/punkt_tab ]; then
  mkdir -p ~/nltk_data/tokenizers
  curl -sS --fail -o /tmp/punkt_tab.zip https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip
  unzip -q -o /tmp/punkt_tab.zip -d ~/nltk_data/tokenizers && rm /tmp/punkt_tab.zip
fi

# Modeles Whisper + alignement francais (besoin de huggingface.co et download.pytorch.org)
~/.reel-kit/venv/bin/python - <<'EOF' || echo "reel-kit: modeles non telecharges, verifier les domaines autorises"
import whisperx
whisperx.load_model("large-v3-turbo", "cpu", compute_type="int8", language="fr", vad_method="silero")
whisperx.load_align_model(language_code="fr", device="cpu")
print("modeles whisperx ok")
EOF
