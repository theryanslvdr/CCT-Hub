import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { CalendarClock, ExternalLink } from 'lucide-react';

const BookingPage = () => {
  const [embedUrl, setEmbedUrl] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await settingsAPI.getBookingEmbed();
        setEmbedUrl(res.data.tidycal_embed_url || '');
      } catch {}
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!embedUrl) {
    return (
      <div className="max-w-3xl mx-auto" data-testid="booking-page">
        <div className="flex items-center gap-3 mb-6">
          <h1 className="text-2xl font-bold text-white">Book a Call</h1>
        </div>
        <Card className="glass-card">
          <CardContent className="py-16 text-center">
            <CalendarClock className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
            <p className="text-zinc-400">Booking calendar not configured yet</p>
            <p className="text-sm text-zinc-500 mt-1">An admin needs to set up the TidyCal embed URL in Settings.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Extract clean URL for iframe src
  const iframeSrc = embedUrl.startsWith('http') ? embedUrl : `https://${embedUrl}`;

  return (
    <div className="max-w-4xl mx-auto" data-testid="booking-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Book a Call</h1>
          <p className="text-sm text-zinc-400 mt-1">Schedule a session using the calendar below</p>
        </div>
        <a
          href={iframeSrc}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-zinc-500 hover:text-orange-400 flex items-center gap-1 transition-colors"
          data-testid="booking-external-link"
        >
          <ExternalLink className="w-3 h-3" /> Open in new tab
        </a>
      </div>
      <Card className="glass-card overflow-hidden">
        <CardContent className="p-0">
          <iframe
            src={iframeSrc}
            title="Book a Call"
            className="w-full border-0"
            style={{ minHeight: '700px', height: '80vh', maxHeight: '900px' }}
            data-testid="booking-iframe"
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default BookingPage;
