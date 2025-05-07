/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }
    document.getElementById('signupBtn').addEventListener('click', function() {
        alert('Thank you for your interest in EduSecure! You will be redirected to the registration page.');
    });

    document.querySelector('.btn-primary').addEventListener('click', function() {
        alert('Redirecting you to the login page...');
    });
    

    const qrCodeVideo = document.getElementById("qr-video");
        const feedbackMessage = document.getElementById("feedbackMessage");

        // Initialize QR Code Scanner
        const html5QrCode = new Html5Qrcode("qr-video");

        // Start the camera to scan QR codes
        html5QrCode.start(
            { facingMode: "environment" }, // Use environment camera
            {
                fps: 10,    // Set frame per second
                qrbox: 250   // QR code box size
            },
            qrCodeMessage => {
                // Handle the scanned QR code message
                feedbackMessage.innerText = `Scanned QR Code: ${qrCodeMessage}`;
            },
            errorMessage => {
                // Handle scanning errors
                console.warn(`QR Code error: ${errorMessage}`);
            })
        .catch(err => {
            console.error(`Unable to start scanning: ${err}`);
        });

        // Stop the scanner when the page is closed or refreshed
        window.addEventListener('beforeunload', () => {
            html5QrCode.stop();
        });

   
});
