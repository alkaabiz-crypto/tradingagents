//+------------------------------------------------------------------+
//| PlanA_EA.mq5 - Plan A from the Exness lab as an MT5 Expert Advisor |
//|                                                                    |
//| Legs (frozen rules, research/exness-lab):                          |
//|  1 BTC NR4      If yesterday's D1 range is the smallest of the last|
//|                 4, place buy-stop at yesterday's high and sell-stop|
//|                 at yesterday's low at 00:00 server. The other level|
//|                 is the stop-loss. One fills -> the other is deleted|
//|                 Close at the next 00:00 server (the daily close).  |
//|  2 BTC Williams Every day at 00:00: buy-stop at today's open + half|
//|                 yesterday's range, sell-stop at open - half. Same  |
//|                 stop, OCO and daily-close exit as NR4.             |
//|  3 ETH > 50-day At 00:00: long while yesterday's D1 close is above |
//|                 the 50-day average of D1 closes, else flat.        |
//|  4 US500 10-day low  At 15:55 New York: if the price is at or below|
//|                 the lowest of the last 10 15:55 prices (today      |
//|                 included), buy. Hold until 3 more 15:55s pass      |
//|                 without a new signal, then sell at 15:55.          |
//| No martingale, no grid, no averaging. One position per leg.        |
//| Kill switch: when closed + open P&L of this EA since InpStartDate  |
//| reaches -InpMaxLossUSD, everything is closed and trading stops.    |
//| Login details are never needed or stored: attach to a chart in a   |
//| terminal you are already logged in to.                             |
//+------------------------------------------------------------------+
#property copyright "tradingagents exness-lab"
#property version   "1.00"
#include <Trade/Trade.mqh>

input group "Symbols (as in Market Watch; an 'm' suffix is tried automatically)"
input string InpBTC   = "BTCUSD";
input string InpETH   = "ETHUSD";
input string InpUS500 = "US500";
input group "Lots (defaults = 2 x Exness minimum, the 20,000 AED paper size)"
input double InpLotNR4      = 0.02;
input double InpLotWilliams = 0.02;
input double InpLotETH      = 0.2;
input double InpLotUS500    = 0.28;
input bool   InpUseNR4 = true, InpUseWilliams = true, InpUseETH = true, InpUseUS500 = true;
input group "Risk"
input double   InpMaxLossUSD = 680;                 // kill switch, account currency
input datetime InpStartDate  = D'2026.11.30 00:00'; // P&L for the kill switch counts from here
input group "Time"
input int InpServerGMTOffset = 0;   // Exness MT5 server time is GMT+0
input int InpUSMinuteNY      = 955; // 15:55 New York, written as HHMM
input group "Magic numbers"
input long InpMagicNR4 = 51001, InpMagicWilliams = 51002, InpMagicETH = 51003, InpMagicUS500 = 51004;

CTrade trade;
string symBTC, symETH, symUS;
string GV_PREFIX = "PlanA_";

//--- helpers --------------------------------------------------------
string Resolve(string s)
  {
   if(SymbolSelect(s, true)) return s;
   if(SymbolSelect(s + "m", true)) return s + "m";
   return "";
  }
void Log(string what)
  {
   Print("PlanA | ", what);
   int h = FileOpen("PlanA_log.csv", FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(h == INVALID_HANDLE) return;
   FileSeek(h, 0, SEEK_END);
   FileWrite(h, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), what);
   FileClose(h);
  }
double NormLot(string s, double lot)
  {
   double step = SymbolInfoDouble(s, SYMBOL_VOLUME_STEP), mn = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), mx = SymbolInfoDouble(s, SYMBOL_VOLUME_MAX);
   lot = MathFloor(lot / step + 1e-9) * step;
   return MathMax(mn, MathMin(mx, lot));
  }
bool HasPosition(string s, long magic)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0 && PositionGetString(POSITION_SYMBOL) == s && PositionGetInteger(POSITION_MAGIC) == magic) return true;
   return false;
  }
void ClosePositions(string s, long magic, string why)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t > 0 && PositionGetString(POSITION_SYMBOL) == s && PositionGetInteger(POSITION_MAGIC) == magic)
        { double pnl = PositionGetDouble(POSITION_PROFIT); trade.SetExpertMagicNumber(magic);
          if(trade.PositionClose(t)) Log(StringFormat("close %s magic %d (%s) pnl %.2f", s, magic, why, pnl)); }
     }
  }
void DeletePendings(string s, long magic)
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong t = OrderGetTicket(i);
      if(t > 0 && OrderGetString(ORDER_SYMBOL) == s && OrderGetInteger(ORDER_MAGIC) == magic) trade.OrderDelete(t);
     }
  }
bool Done(string key)  { return GlobalVariableCheck(GV_PREFIX + key); }
void Mark(string key)  { GlobalVariableSet(GV_PREFIX + key, 1); }
string DayKey(datetime t) { return TimeToString(t, TIME_DATE); }

//--- New York time from server time (US DST: 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC)
datetime NthSunday(int year, int month, int n)
  {
   MqlDateTime d; d.year = year; d.mon = month; d.day = 1; d.hour = 0; d.min = 0; d.sec = 0;
   datetime t = StructToTime(d); MqlDateTime w; TimeToStruct(t, w);
   int first = (7 - w.day_of_week) % 7; // days to the first Sunday
   return t + (first + 7 * (n - 1)) * 86400;
  }
int NYOffsetHours(datetime utc)
  {
   MqlDateTime d; TimeToStruct(utc, d);
   datetime start = NthSunday(d.year, 3, 2) + 7 * 3600, end = NthSunday(d.year, 11, 1) + 6 * 3600;
   return (utc >= start && utc < end) ? -4 : -5;
  }
// server time of HH:MM New York on the New York date that contains server time t
datetime ServerTimeOfNY(datetime serverT, int hhmm)
  {
   datetime utc = serverT - InpServerGMTOffset * 3600;
   datetime ny = utc + NYOffsetHours(utc) * 3600;
   datetime nyMidnight = ny - (ny % 86400);
   datetime nyT = nyMidnight + (hhmm / 100) * 3600 + (hhmm % 100) * 60;
   datetime utcT = nyT - NYOffsetHours(nyT + 5 * 3600) * 3600;
   return utcT + InpServerGMTOffset * 3600;
  }

//--- order placement for the two BTC breakout legs
void PlaceStraddle(string s, long magic, double lot, double up, double dn, string tag)
  {
   trade.SetExpertMagicNumber(magic);
   double ask = SymbolInfoDouble(s, SYMBOL_ASK), bid = SymbolInfoDouble(s, SYMBOL_BID);
   int dg = (int)SymbolInfoInteger(s, SYMBOL_DIGITS);
   up = NormalizeDouble(up, dg); dn = NormalizeDouble(dn, dg); lot = NormLot(s, lot);
   datetime exp = 0; // removed by the EA at the next daily run
   // if the price already trades beyond a level, the backtest fills at the open: use a market order
   if(ask >= up) { if(trade.Buy(lot, s, 0, dn, 0, tag)) Log(StringFormat("%s market buy %.2f %s sl %s (price already above the level)", tag, lot, s, DoubleToString(dn, dg))); return; }
   if(bid <= dn) { if(trade.Sell(lot, s, 0, up, 0, tag)) Log(StringFormat("%s market sell %.2f %s sl %s (price already below the level)", tag, lot, s, DoubleToString(up, dg))); return; }
   bool a = trade.BuyStop(lot, up, s, dn, 0, ORDER_TIME_GTC, exp, tag);
   bool b = trade.SellStop(lot, dn, s, up, 0, ORDER_TIME_GTC, exp, tag);
   Log(StringFormat("%s %s buy-stop %s / sell-stop %s lot %.2f (%s/%s)", tag, s, DoubleToString(up, dg), DoubleToString(dn, dg), lot, a ? "ok" : "FAIL", b ? "ok" : "FAIL"));
  }
// one filled -> delete the other (OCO)
void EnforceOCO(string s, long magic) { if(HasPosition(s, magic)) DeletePendings(s, magic); }

//--- kill switch
double EAProfitSince(datetime from)
  {
   double p = 0; long mags[4]; mags[0] = InpMagicNR4; mags[1] = InpMagicWilliams; mags[2] = InpMagicETH; mags[3] = InpMagicUS500;
   if(HistorySelect(from, TimeCurrent() + 86400))
      for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
        {
         ulong d = HistoryDealGetTicket(i); long m = HistoryDealGetInteger(d, DEAL_MAGIC);
         for(int k = 0; k < 4; k++) if(m == mags[k]) p += HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
        }
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0) { long m = PositionGetInteger(POSITION_MAGIC); for(int k = 0; k < 4; k++) if(m == mags[k]) p += PositionGetDouble(POSITION_PROFIT); }
   return p;
  }
void KillAll(string why)
  {
   ClosePositions(symBTC, InpMagicNR4, why); ClosePositions(symBTC, InpMagicWilliams, why); ClosePositions(symETH, InpMagicETH, why); ClosePositions(symUS, InpMagicUS500, why);
   DeletePendings(symBTC, InpMagicNR4); DeletePendings(symBTC, InpMagicWilliams);
   Mark("KILLED"); Log("KILL SWITCH: " + why + ". Trading stopped. Delete global variable PlanA_KILLED (F3) to restart.");
  }

//--- daily crypto run, right after 00:00 server (the D1 close)
void CryptoDaily()
  {
   datetime now = TimeCurrent(); string key = "crypto_" + DayKey(now);
   if(Done(key)) return;
   if(iTime(symBTC, PERIOD_D1, 0) < now - (now % 86400)) return; // today's D1 bar not formed yet
   // exits at the daily close: yesterday's breakout trades and unfilled orders
   ClosePositions(symBTC, InpMagicNR4, "daily close"); ClosePositions(symBTC, InpMagicWilliams, "daily close");
   DeletePendings(symBTC, InpMagicNR4); DeletePendings(symBTC, InpMagicWilliams);
   double h1 = iHigh(symBTC, PERIOD_D1, 1), l1 = iLow(symBTC, PERIOD_D1, 1), o0 = iOpen(symBTC, PERIOD_D1, 0), r1 = h1 - l1;
   if(InpUseNR4)
     {
      bool nr4 = true;
      for(int k = 2; k <= 4; k++) if(iHigh(symBTC, PERIOD_D1, k) - iLow(symBTC, PERIOD_D1, k) < r1) nr4 = false;
      if(nr4) PlaceStraddle(symBTC, InpMagicNR4, InpLotNR4, h1, l1, "PlanA NR4");
      else Log("NR4: no setup");
     }
   if(InpUseWilliams && r1 > 0) PlaceStraddle(symBTC, InpMagicWilliams, InpLotWilliams, o0 + 0.5 * r1, o0 - 0.5 * r1, "PlanA Williams");
   if(InpUseETH)
     {
      double s = 0; for(int k = 1; k <= 50; k++) s += iClose(symETH, PERIOD_D1, k);
      double sma = s / 50, c1 = iClose(symETH, PERIOD_D1, 1); bool want = c1 > sma, have = HasPosition(symETH, InpMagicETH);
      trade.SetExpertMagicNumber(InpMagicETH);
      if(want && !have && trade.Buy(NormLot(symETH, InpLotETH), symETH, 0, 0, 0, "PlanA ETH50")) Log(StringFormat("ETH buy: close %.2f > SMA50 %.2f", c1, sma));
      if(!want && have) ClosePositions(symETH, InpMagicETH, StringFormat("close %.2f <= SMA50 %.2f", c1, sma));
      if(want == have) Log(StringFormat("ETH %s (close %.2f, SMA50 %.2f)", have ? "hold" : "flat", c1, sma));
     }
   Mark(key);
  }

//--- US500 10-day low, at 15:55 New York
double PriceAt(string s, datetime t)  // close of the M1 bar that ends at t (price at t)
  {
   int sh = iBarShift(s, PERIOD_M1, t - 60, false);
   if(sh < 0) return 0;
   datetime bt = iTime(s, PERIOD_M1, sh);
   if(bt > t - 60 || bt < t - 600) return 0; // no trading in the 10 minutes before t: not a trading day
   return iClose(s, PERIOD_M1, sh);
  }
void USDaily()
  {
   datetime now = TimeCurrent(); datetime t0 = ServerTimeOfNY(now, InpUSMinuteNY);
   if(now < t0 || now > t0 + 240) return;
   string key = "us_" + DayKey(t0); if(Done(key)) return;
   MqlDateTime w; datetime u0 = t0 - InpServerGMTOffset * 3600; TimeToStruct(u0 + NYOffsetHours(u0) * 3600, w);
   if(w.day_of_week == 0 || w.day_of_week == 6) { Mark(key); return; }
   // 15:55 prices for today (live) and the previous trading days, newest first
   double px[]; ArrayResize(px, 0);
   ArrayResize(px, 1); px[0] = SymbolInfoDouble(symUS, SYMBOL_BID);
   for(int d = 1; d <= 25 && ArraySize(px) < 13; d++)
     {
      double p = PriceAt(symUS, ServerTimeOfNY(now - d * 86400, InpUSMinuteNY));
      if(p > 0) { int n = ArraySize(px); ArrayResize(px, n + 1); px[n] = p; }
     }
   if(ArraySize(px) < 13) { Log("US500: not enough M1 history for 12 prior 15:55 prices"); return; }
   // signal on day j (0 = today): px[j] <= min(px[j..j+9])
   bool sig[3];
   for(int j = 0; j < 3; j++) { double m = px[j]; for(int k = j; k < j + 10; k++) m = MathMin(m, px[k]); sig[j] = px[j] <= m; }
   bool want = sig[0] || sig[1] || sig[2], have = HasPosition(symUS, InpMagicUS500);
   trade.SetExpertMagicNumber(InpMagicUS500);
   if(want && !have && trade.Buy(NormLot(symUS, InpLotUS500), symUS, 0, 0, 0, "PlanA US500 10d low")) Log(StringFormat("US500 buy at %.2f (10-day low)", px[0]));
   if(!want && have) ClosePositions(symUS, InpMagicUS500, "3 closes after the last 10-day low");
   if(want == have) Log(StringFormat("US500 %s (price %.2f, signals today/1/2 days ago %d%d%d)", have ? "hold" : "flat", px[0], sig[0], sig[1], sig[2]));
   Mark(key);
  }

//--- events -----------------------------------------------------------
int OnInit()
  {
   symBTC = Resolve(InpBTC); symETH = Resolve(InpETH); symUS = Resolve(InpUS500);
   if(symBTC == "" || symETH == "" || symUS == "") { Alert("PlanA: a symbol was not found in Market Watch. Check the symbol inputs."); return INIT_PARAMETERS_INCORRECT; }
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     { Alert("PlanA needs a HEDGING account (NR4 and Williams can both hold BTC)."); return INIT_FAILED; }
   trade.SetDeviationInPoints(50);
   EventSetTimer(20);
   Log(StringFormat("start: %s %s %s, lots NR4 %.2f W %.2f ETH %.2f US500 %.2f, kill at -%.0f", symBTC, symETH, symUS, InpLotNR4, InpLotWilliams, InpLotETH, InpLotUS500, InpMaxLossUSD));
   return INIT_SUCCEEDED;
  }
void OnDeinit(const int reason) { EventKillTimer(); }
void OnTimer()
  {
   if(Done("KILLED")) return;
   if(EAProfitSince(InpStartDate) <= -InpMaxLossUSD) { KillAll(StringFormat("loss reached -%.0f", InpMaxLossUSD)); return; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return;
   EnforceOCO(symBTC, InpMagicNR4); EnforceOCO(symBTC, InpMagicWilliams);
   CryptoDaily();
   if(InpUseUS500) USDaily();
  }
void OnTick() { if(!Done("KILLED")) { EnforceOCO(symBTC, InpMagicNR4); EnforceOCO(symBTC, InpMagicWilliams); } }
//+------------------------------------------------------------------+
