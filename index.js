import express from 'express';
import cors from 'cors';
import { Resend } from 'resend';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const app = express();
const port = process.env.PORT || 3000;

app.set('trust proxy', true);  // trust GitHub proxy/tunnel

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const resend = new Resend('re_jmkZBHee_DkrfMr3eML2BMH4jkY7kwJYY');
const recipientEmail = 'LycanDev@hotmail.com';

app.use(cors());
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

// Log all incoming requests
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.originalUrl}`);
  next();
});

app.post('/api/request', async (req, res) => {
  console.log('Handling POST /api/request', req.body);
  try {
    await resend.emails.send({
      from: 'Acme <onboarding@resend.dev>',
      to: recipientEmail,
      subject: 'New Custom Software Request',
      html: `<strong>From:</strong> ${req.body.name} (${req.body.email})<br/><br/><strong>Description:</strong><br/>${req.body.description.replace(/\n/g, '<br/>')}`
    });
    res.status(200).json({ success: true });
  } catch (err) {
    console.error('Email send error:', err);
    res.status(500).json({ success: false, error: 'Email failed to send.' });
  }
});

app.use(express.static(path.join(__dirname)));

app.get('/custom-request', (req, res) => {
  res.sendFile(path.join(__dirname, 'custom-request.html'));
});

app.use((req, res) => res.status(404).send('Route not found'));

app.listen(port, '0.0.0.0', () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});
