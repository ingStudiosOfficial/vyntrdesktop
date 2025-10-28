function redirectToDownload() {
    document.getElementById('download-button-windows').addEventListener('click', () => {
        window.open('https://github.com/ingStudiosOfficial/vyntrdesktop/releases/latest/download/vyntrdesktop_windows.exe', '_blank')
    });

    document.getElementById('download-button-linux').addEventListener('click', () => {
        window.open('https://github.com/ingStudiosOfficial/vyntrdesktop/releases/latest/download/vyntrdesktop_linux', '_blank')
    });
}

document.addEventListener('DOMContentLoaded', () => {
    redirectToDownload();
});