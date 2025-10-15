function redirectToDownload() {
    document.getElementById('download-button').addEventListener('click', () => {
        window.open('https://github.com/ingStudiosOfficial/vyntrdesktop/releases/latest/download/Vyntr.For.Desktop.exe', '_blank')
    });
}

document.addEventListener('DOMContentLoaded', () => {
    redirectToDownload();
});