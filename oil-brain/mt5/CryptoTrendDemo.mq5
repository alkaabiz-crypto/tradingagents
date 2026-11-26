//+------------------------------------------------------------------+
//| CryptoTrendDemo.mq5 - the lab's crypto trend day trade, DEMO ONLY |
//| Rule (frozen, same as oil-brain/live/crypto_trend_ticket.py):     |
//|  each server day (Exness server = GMT+0 = UTC), for each symbol:   |
//|   LONG if yesterday's D1 close > 50-day average, else SHORT;       |
//|   enter just after the day opens; stop 0.5 x ATR14 (simple mean of |
//|   true range, D1); size = BalancePerCoin x min(1, 2% / ATR%);      |
//|   no target; close at the next day's open (midnight UTC).          |
//|  Kill switch: stops trading if the EA's closed P&L falls more than |
//|   15% of the total balance below its peak.                         |
//| It REFUSES to run on a real account. Research, not advice.        |
//+------------------------------------------------------------------+
#property copyright "tradingagents lab (paper/demo research)"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

input string InpSymbols        = "BTCUSD,ETHUSD"; // symbols (add the suffix if your account uses one, e.g. BTCUSDm)
input double InpTotalBalance   = 3400;            // $ for the whole strategy (split equally between the symbols)
input int    InpSmaDays        = 50;              // trend average (days)
input int    InpAtrDays        = 14;              // ATR length (days)
input double InpStopAtr        = 0.5;             // stop distance in ATR
input double InpVolTarget      = 0.02;            // vol sizing: weight = min(1, this / ATR%)
input double InpKillDrawdown   = 0.15;            // kill switch: stop if closed P&L is 15% of total below its peak
input int    InpEntryDelayMin  = 1;               // minutes after the day opens before entering
input long   InpMagic          = 26112601;        // magic number for this EA's trades
input int    InpDeviationPts   = 200;             // max price deviation for market orders (points)

CTrade  trade;
string  syms[];
bool    killed = false;

//+------------------------------------------------------------------+
int OnInit()
  {
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      Alert("CryptoTrendDemo: this is NOT a demo account. The EA is demo-only and will not trade.");
      return(INIT_FAILED);
     }
   int n = StringSplit(InpSymbols, ',', syms);
   if(n <= 0) return(INIT_PARAMETERS_INCORRECT);
   for(int i = 0; i < n; i++)
     {
      StringTrimLeft(syms[i]); StringTrimRight(syms[i]);
      if(!SymbolSelect(syms[i], true))
        { Alert("CryptoTrendDemo: symbol not found: ", syms[i]); return(INIT_PARAMETERS_INCORRECT); }
     }
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpDeviationPts);
   EventSetTimer(30);
   Print("CryptoTrendDemo started on DEMO: ", InpSymbols, ", total $", DoubleToString(InpTotalBalance, 0));
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason) { EventKillTimer(); }

//+------------------------------------------------------------------+
datetime DayStart(datetime t) { return(t - (t % 86400)); }

// simple-mean ATR and SMA from completed D1 bars (shift 1 = yesterday)
bool Signals(const string s, int &dir, double &atr, double &lastClose, double &sma)
  {
   MqlRates r[];
   int need = MathMax(InpSmaDays, InpAtrDays + 1) + 2;
   ArraySetAsSeries(r, true);
   if(CopyRates(s, PERIOD_D1, 1, need, r) < need) return(false);   // r[0] = yesterday
   lastClose = r[0].close;
   double sum = 0; for(int i = 0; i < InpSmaDays; i++) sum += r[i].close; sma = sum / InpSmaDays;
   double tr = 0;
   for(int i = 0; i < InpAtrDays; i++)
     {
      double pc = r[i + 1].close;
      tr += MathMax(r[i].high - r[i].low, MathMax(MathAbs(r[i].high - pc), MathAbs(r[i].low - pc)));
     }
   atr = tr / InpAtrDays;
   dir = (lastClose > sma) ? 1 : -1;
   return(atr > 0);
  }

double Lots(const string s, double notional, double price)
  {
   double cs = SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE);
   double step = SymbolInfoDouble(s, SYMBOL_VOLUME_STEP), vmin = SymbolInfoDouble(s, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(s, SYMBOL_VOLUME_MAX);
   if(cs <= 0 || step <= 0 || price <= 0) return(0);
   double raw = notional / (price * cs);
   double lots = MathRound(raw / step) * step;          // same rounding as the Python ticket
   if(lots < vmin) return(0);                            // too small for this account: skip, never size up
   return(MathMin(lots, vmax));
  }

bool HasPosition(const string s, datetime &opened)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == s && PositionGetInteger(POSITION_MAGIC) == InpMagic)
        { opened = (datetime)PositionGetInteger(POSITION_TIME); return(true); }
     }
   return(false);
  }

bool EnteredToday(const string s, datetime day0)
  {
   if(!HistorySelect(day0, TimeTradeServer() + 60)) return(false);
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
     {
      ulong d = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(d, DEAL_MAGIC) == InpMagic && HistoryDealGetString(d, DEAL_SYMBOL) == s &&
         HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN) return(true);
     }
   return(false);
  }

bool KillSwitch()
  {
   if(!HistorySelect(0, TimeTradeServer() + 60)) return(false);
   double eq = 0, peak = 0, worst = 0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
     {
      ulong d = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(d, DEAL_MAGIC) != InpMagic) continue;
      eq += HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_SWAP) + HistoryDealGetDouble(d, DEAL_COMMISSION);
      peak = MathMax(peak, eq); worst = MathMin(worst, eq - peak);
     }
   return(worst < -InpKillDrawdown * InpTotalBalance);
  }

//+------------------------------------------------------------------+
void OnTimer()
  {
   datetime now = TimeTradeServer(), day0 = DayStart(now);
   int n = ArraySize(syms);
   // 1) close yesterday's positions (the day trade ends at midnight server time)
   for(int i = 0; i < n; i++)
     {
      datetime opened;
      if(HasPosition(syms[i], opened) && opened < day0)
         if(!trade.PositionClose(syms[i])) Print("close failed ", syms[i], " ", trade.ResultRetcodeDescription());
     }
   if(killed) return;
   if(KillSwitch())
     {
      killed = true;
      Alert("CryptoTrendDemo KILL SWITCH: closed P&L fell more than ", DoubleToString(InpKillDrawdown * 100, 0),
            "% of the total below its peak. Trading stopped - review with the lab.");
      return;
     }
   if(now < day0 + InpEntryDelayMin * 60) return;
   // 2) one entry per symbol per day
   double perCoin = InpTotalBalance / n;
   for(int i = 0; i < n; i++)
     {
      string s = syms[i]; datetime opened;
      if(HasPosition(s, opened) || EnteredToday(s, day0)) continue;
      int dir; double atr, c, sma;
      if(!Signals(s, dir, atr, c, sma)) continue;
      double w = MathMin(1.0, InpVolTarget / (atr / c));
      double price = (dir > 0) ? SymbolInfoDouble(s, SYMBOL_ASK) : SymbolInfoDouble(s, SYMBOL_BID);
      double lots = Lots(s, perCoin * w, price);
      if(lots <= 0)
        { Print(s, ": rule size $", DoubleToString(perCoin * w, 0), " is below the minimum lot - skipped today"); continue; }
      int dg = (int)SymbolInfoInteger(s, SYMBOL_DIGITS);
      double sl = NormalizeDouble(price - dir * InpStopAtr * atr, dg);
      bool ok = (dir > 0) ? trade.Buy(lots, s, 0, sl, 0, "lab crypto trend") : trade.Sell(lots, s, 0, sl, 0, "lab crypto trend");
      Print(s, (dir > 0 ? " BUY " : " SELL "), DoubleToString(lots, 2), " lots, SL ", DoubleToString(sl, dg),
            " (close ", DoubleToString(c, dg), " vs SMA", InpSmaDays, " ", DoubleToString(sma, dg), ") ",
            ok ? "OK" : trade.ResultRetcodeDescription());
     }
  }
//+------------------------------------------------------------------+
