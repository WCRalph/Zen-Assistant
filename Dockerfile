ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache python3 py3-pip alsa-utils

# Set the working directory
WORKDIR /usr/src/zen_assistant

# Copy the add-on files
COPY run.sh /
COPY zen_assistant/ ./zen_assistant/

# Install Python dependencies
RUN pip3 install --no-cache-dir pydub pyaudio numpy aiohttp voluptuous

# Make the run script executable
RUN chmod a+x /run.sh

# Command to run the add-on
CMD [ "/run.sh" ]
