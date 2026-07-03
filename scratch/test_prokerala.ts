import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

async function test() {
  const credentials = Buffer.from(`${process.env.PROKERALA_CLIENT_ID}:${process.env.PROKERALA_CLIENT_SECRET}`).toString('base64');
  try {
    const response = await axios.post(
      'https://api.prokerala.com/token',
      'grant_type=client_credentials',
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Authorization: `Basic ${credentials}`,
        },
      }
    );
    const token = response.data.access_token;
    
    // Let's print out what planet-position returns in production
    try {
      const res = await axios.get('https://api.prokerala.com/v2/astrology/planet-position', {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        params: {
          datetime: '1995-11-20T10:30:00+05:30', 
          coordinates: '28.6138954,77.2090057',
          ayanamsa: 1
        }
      });
      // Print the whole response payload
      console.log('Planet positions payload:', JSON.stringify(res.data, null, 2));
    } catch (e: any) {
      console.error('Planet position request failed:', e.response?.status, JSON.stringify(e.response?.data, null, 2));
    }
  } catch (e: any) {
    console.error('Auth failed:', e.response?.status, e.response?.data || e.message);
  }
}

test();
