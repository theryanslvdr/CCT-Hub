import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { toast } from 'sonner';
import {
  TrendingUp, TreePine, Calendar as CalendarIcon, Loader2, Plus,
  Trash2, Eye, EyeOff
} from 'lucide-react';

export function TradingTab() {
  const [globalHolidays, setGlobalHolidays] = useState([]);
  const [holidaysLoading, setHolidaysLoading] = useState(false);
  const [selectedHolidayMonth, setSelectedHolidayMonth] = useState(new Date());
  const [savingHoliday, setSavingHoliday] = useState(false);

  const [tradingProducts, setTradingProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [newProductName, setNewProductName] = useState('');
  const [savingProduct, setSavingProduct] = useState(false);

  useEffect(() => {
    loadGlobalHolidays();
    loadTradingProducts();
  }, []);

  const loadGlobalHolidays = async () => {
    setHolidaysLoading(true);
    try {
      const res = await adminAPI.getGlobalHolidays();
      setGlobalHolidays(res.data.holidays || []);
    } catch (error) {
      console.error('Failed to load global holidays:', error);
    } finally {
      setHolidaysLoading(false);
    }
  };

  const toggleHoliday = async (date) => {
    const dateStr = date.toISOString().split('T')[0];
    const existingHoliday = globalHolidays.find((h) => h.date === dateStr);
    setSavingHoliday(true);
    try {
      if (existingHoliday) {
        await adminAPI.removeGlobalHoliday(dateStr);
        toast.success('Holiday removed');
      } else {
        await adminAPI.addGlobalHoliday(dateStr, 'Market Holiday');
        toast.success('Holiday added');
      }
      loadGlobalHolidays();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update holiday');
    } finally {
      setSavingHoliday(false);
    }
  };

  const isHoliday = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return globalHolidays.some((h) => h.date === dateStr);
  };

  const loadTradingProducts = async () => {
    setProductsLoading(true);
    try {
      const res = await adminAPI.getTradingProducts();
      setTradingProducts(res.data.products || []);
    } catch (error) {
      console.error('Failed to load trading products:', error);
    } finally {
      setProductsLoading(false);
    }
  };

  const handleAddProduct = async () => {
    if (!newProductName.trim()) {
      toast.error('Please enter a product name');
      return;
    }
    setSavingProduct(true);
    try {
      await adminAPI.addTradingProduct(newProductName.trim());
      toast.success('Product added');
      setNewProductName('');
      loadTradingProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add product');
    } finally {
      setSavingProduct(false);
    }
  };

  const handleRemoveProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to remove this product?')) return;
    try {
      await adminAPI.removeTradingProduct(productId);
      toast.success('Product removed');
      loadTradingProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove product');
    }
  };

  const handleToggleProduct = async (product) => {
    try {
      await adminAPI.updateTradingProduct(product.id, { is_active: !product.is_active });
      toast.success(`Product ${product.is_active ? 'disabled' : 'enabled'}`);
      loadTradingProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update product');
    }
  };

  return (
    <div className="space-y-6">
      {/* Trading Products Card */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-400" /> Trading Products
          </CardTitle>
          <p className="text-sm text-zinc-400 mt-1">Manage the list of tradeable products available to all users.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={newProductName}
              onChange={(e) => setNewProductName(e.target.value.toUpperCase())}
              placeholder="Enter product name (e.g., BTCUSD)"
              className="input-dark flex-1"
              data-testid="new-product-input"
            />
            <Button
              onClick={handleAddProduct}
              disabled={savingProduct || !newProductName.trim()}
              className="btn-primary gap-2"
              data-testid="add-product-btn"
            >
              {savingProduct ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add
            </Button>
          </div>

          {productsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : (
            <div className="space-y-2">
              {tradingProducts.map((product) => (
                <div
                  key={product.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    product.is_active
                      ? 'bg-zinc-900/50 border-zinc-700'
                      : 'bg-zinc-900/30 border-zinc-800 opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`font-mono text-lg ${product.is_active ? 'text-white' : 'text-zinc-500'}`}>
                      {product.name}
                    </span>
                    {!product.is_active && (
                      <span className="text-xs bg-zinc-700 text-zinc-400 px-2 py-0.5 rounded">Disabled</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleToggleProduct(product)}
                      className={`h-8 ${
                        product.is_active
                          ? 'text-amber-400 hover:bg-amber-500/10'
                          : 'text-emerald-400 hover:bg-emerald-500/10'
                      }`}
                    >
                      {product.is_active ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRemoveProduct(product.id)}
                      className="h-8 text-red-400 hover:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {tradingProducts.length === 0 && (
                <p className="text-center text-zinc-500 py-4">No products configured</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Global Holidays Card */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TreePine className="w-5 h-5 text-emerald-400" /> Global Market Holidays
          </CardTitle>
          <p className="text-sm text-zinc-400 mt-1">
            Click dates to toggle holidays. Holidays will skip streak calculations for all users.
          </p>
        </CardHeader>
        <CardContent>
          {holidaysLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : (
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex justify-center">
                <Calendar
                  mode="single"
                  selected={null}
                  month={selectedHolidayMonth}
                  onMonthChange={setSelectedHolidayMonth}
                  onDayClick={(day) => toggleHoliday(day)}
                  modifiers={{ holiday: (date) => isHoliday(date) }}
                  modifiersStyles={{
                    holiday: {
                      backgroundColor: 'rgb(239 68 68 / 0.2)',
                      color: '#ef4444',
                      fontWeight: 'bold',
                      borderRadius: '6px',
                    },
                  }}
                  className="rounded-lg border border-zinc-700 bg-zinc-900/50 p-3"
                  disabled={savingHoliday}
                />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                  <CalendarIcon className="w-4 h-4 text-red-400" /> Active Holidays ({globalHolidays.length})
                </p>
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {globalHolidays.length === 0 ? (
                    <p className="text-sm text-zinc-500">No holidays configured</p>
                  ) : (
                    globalHolidays
                      .sort((a, b) => a.date.localeCompare(b.date))
                      .map((h) => (
                        <div
                          key={h.date}
                          className="flex items-center justify-between p-2 rounded bg-zinc-800/50 text-sm"
                        >
                          <span className="text-zinc-300">{h.date}</span>
                          <span className="text-zinc-500 text-xs">{h.name}</span>
                        </div>
                      ))
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
