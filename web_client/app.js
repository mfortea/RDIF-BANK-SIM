require('dotenv').config();
const express = require('express');
const mariadb = require('mariadb');

const app = express();
const port = process.env.SERVER_PORT;

// Conexión a la base de datos
const pool = mariadb.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME
});

app.get('/prices', async (req, res) => {
    try {
        const connection = await pool.getConnection();
        const rows = await connection.query("SELECT * FROM prices");
        connection.end();
        res.json(rows[0]);
    } catch (err) {
        console.error(err);
        res.status(500).send("Server Error");
    }
});

app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Precios de Combustible</title>
            <link rel="stylesheet" href="/style.css">
        </head>
        <body>
            <div class="fuel-prices">
                <div class="price-item">
                    <h2>GASOLINE</h2>
                    <p id="gasolinePrice">--.--</p>
                </div>
                <div class="price-item">
                    <h2>DIESEL</h2>
                    <p id="dieselPrice">--.--</p>
                </div>
            </div>
            <script src="/script.js"></script>
        </body>
        </html>
    `);
});

app.use(express.static('public'));

app.listen(port, () => {
    console.log(`Server running: http://localhost:${port}`);
});
