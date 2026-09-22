'use strict';

let activeRecorder = null;
let activeStream = null;
let activeForm = null;
let isStarting = false;

function setVoiceState(form, state, message) {
    const button = form.querySelector('[data-voice]');
    const status = form.querySelector('[data-voice-status]');
    if (!button || !status) return;

    button.disabled = state === 'transcribing';
    button.innerHTML = state === 'recording'
        ? 'Stop'
        : '<img src="../assets/microphone.png" alt="" aria-hidden="true">';
    status.textContent = message;
    form.dataset.voiceState = state;
}

function insertTranscript(input, transcript) {
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? start;
    const before = input.value.slice(0, start);
    const after = input.value.slice(end);
    const separator = before && !/\s$/.test(before) ? ' ' : '';
    input.value = `${before}${separator}${transcript}${after}`;
    const cursor = before.length + separator.length + transcript.length;
    input.setSelectionRange(cursor, cursor);
    input.focus();
    input.dispatchEvent(new Event('input', { bubbles: true }));
}

async function transcribe(form, input, chunks, mimeType) {
    activeRecorder = null;
    activeForm = null;
    activeStream?.getTracks().forEach(track => track.stop());
    activeStream = null;
    setVoiceState(form, 'transcribing', 'Transcribing locally...');

    try {
        const blob = new Blob(chunks, { type: mimeType });
        const filename = mimeType.includes('mp4') ? 'brain-dump.m4a' : 'brain-dump.webm';
        const response = await fetch('/api/transcriptions', {
            method: 'POST',
            body: (() => {
                const data = new FormData();
                data.append('audio', blob, filename);
                return data;
            })()
        });
        if (!response.ok) throw new Error(`Transcription failed (${response.status})`);
        const result = await response.json();
        insertTranscript(input, result.transcript);
        setVoiceState(form, 'ready', '');
    } catch (error) {
        setVoiceState(form, 'error', 'Voice capture failed. Typing still works.');
        input.focus();
    }
}

async function startRecording(form, input) {
    if (activeRecorder || isStarting) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        setVoiceState(form, 'error', 'Voice recording is not available in this browser.');
        input.focus();
        return;
    }

    isStarting = true;
    activeForm = form;
    try {
        activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mimeTypes = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'];
        const mimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || '';
        activeRecorder = new MediaRecorder(activeStream, mimeType ? { mimeType } : undefined);
        const chunks = [];
        activeRecorder.addEventListener('dataavailable', event => {
            if (event.data.size) chunks.push(event.data);
        });
        activeRecorder.addEventListener('stop', () => transcribe(form, input, chunks, mimeType));
        activeRecorder.start();
        setVoiceState(form, 'recording', 'Recording... Press Stop when ready.');
    } catch (error) {
        activeStream?.getTracks().forEach(track => track.stop());
        activeStream = null;
        activeForm = null;
        setVoiceState(form, 'error', 'Microphone permission was not granted.');
        input.focus();
    } finally {
        isStarting = false;
    }
}

document.addEventListener('click', event => {
    const button = event.target.closest('[data-voice]');
    if (!button) return;
    const form = button.closest('form');
    const input = form?.querySelector('textarea');
    if (!form || !input) return;
    event.preventDefault();

    if (activeRecorder && form === activeForm) {
        setVoiceState(form, 'transcribing', 'Preparing audio...');
        activeRecorder.stop();
    } else if (!activeRecorder && !isStarting) {
        startRecording(form, input);
    }
});
