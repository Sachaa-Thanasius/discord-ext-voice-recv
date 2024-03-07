from setuptools import setup


def derive_version() -> str:
    import re

    with open('discord/ext/voice_recv/__init__.py') as f:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)  # type: ignore

    if not version:
        raise RuntimeError('version is not set')

    if version.endswith(('a', 'b', 'rc')):
        # append version identifier based on commit count
        try:
            import subprocess

            PIPE = subprocess.PIPE

            with subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'], stdout=PIPE, stderr=PIPE) as p:
                out, err = p.communicate()
                if out:
                    version = version + out.decode('utf-8').strip()
        except Exception:
            pass
    return version


setup(version=derive_version())
