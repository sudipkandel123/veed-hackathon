echo "WARNING: /Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER/etc/profile.d/mamba.sh (the file emitting this warning) is deprecated."
echo "WARNING: This file will be removed on the next release after 30th September 2025."
echo "WARNING: Please use 'mamba shell init' to get the correct initialization for your shell."

if [ -z "" ]; then
    echo "WARNING: The MAMBA_ROOT_PREFIX environment variable is not set."
    echo "WARNING: This is required for mamba to work correctly as of 2.0."
    echo "WARNING: "
    echo "WARNING: For now, we are setting 'MAMBA_ROOT_PREFIX' to '/Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER'."
    echo "WARNING: "
    echo "WARNING: Please make sure this is consistent with your installation or alternatively (by order of preference):"
    echo "WARNING:   - rerun 'mamba shell init' to initialize mamba for your current shell"
    echo "WARNING:   - manually set 'MAMBA_ROOT_PREFIX' to the root of your installation in your shell profile script."
    echo "WARNING:   - use the '-r,--root-prefix' CLI option when calling mamba."
    echo "WARNING: "
    echo "WARNING: This message originates from /Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER/etc/profile.d/mamba.sh"
    export MAMBA_ROOT_PREFIX="/Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER"
fi

__mamba_setup="$("/Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER/bin/mamba" shell hook --shell posix 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias mamba="/Users/sudipkandel/Desktop/Mac/code/hackathon/veed.io/ENTER/bin/mamba"  # Fallback on help from mamba activate
fi
unset __mamba_setup
