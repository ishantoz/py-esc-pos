const express = require('express');
const multer = require('multer');
const qz = require('qz-tray');
const app = express();
const upload = multer({ storage: multer.memoryStorage() });


async function printSomething() {
  try {
    await qz.connect(); // wait for QZ Tray connection

    const printers = await qz.printers.find();
    console.log('Available printers:', printers);

    const printerName = 'Your Rongta Printer Name'; // exact name

    const config = qz.configs.create(printerName);

    const data = [
      '\x1B' + '\x40', // ESC @ initialize printer
      'Hello Rongta!\n',
      '\x1D' + 'V' + '\x41' + '\x03' // cut paper command
    ];

    await qz.print(config, data);

    await qz.disconnect(); // optional, close connection when done
  } catch (error) {
    console.error('Printing error:', error);
  }
}

printSomething();
