import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Signal, 
  BarChart3,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Target,
  Users,
  DollarSign,
  AlertTriangle
} from 'lucide-react'
import './App.css'

const API_BASE = 'http://localhost:5000'

function App() {
  const [dashboardStats, setDashboardStats] = useState(null)
  const [recentSignals, setRecentSignals] = useState([])
  const [topWallets, setTopWallets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/api/dashboard/stats`)
      if (!response.ok) throw new Error('فشل في جلب البيانات')
      
      const data = await response.json()
      setDashboardStats(data.stats)
      setRecentSignals(data.recent_signals || [])
      setTopWallets(data.top_wallets || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'FAILURE':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'PENDING':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <Eye className="h-4 w-4 text-gray-500" />
    }
  }

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case 'STRONG_BUY':
        return <Badge className="bg-green-600 text-white">شراء قوي</Badge>
      case 'BUY':
        return <Badge className="bg-green-400 text-white">شراء</Badge>
      case 'IGNORE':
        return <Badge variant="secondary">تجاهل</Badge>
      default:
        return <Badge variant="outline">غير محدد</Badge>
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-white text-xl">جاري تحميل البيانات...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <p className="text-white text-xl mb-4">خطأ في تحميل البيانات</p>
          <p className="text-red-300 mb-6">{error}</p>
          <Button onClick={fetchDashboardData} variant="outline">
            إعادة المحاولة
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 rtl:space-x-reverse">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-3 rounded-lg">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  الصقر الذكي
                </h1>
                <p className="text-slate-400 text-sm">نظام تحليل العملات الرقمية المتقدم</p>
              </div>
            </div>
            <Button onClick={fetchDashboardData} variant="outline" size="sm">
              <Activity className="h-4 w-4 mr-2" />
              تحديث البيانات
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">إجمالي الإشارات</CardTitle>
              <Signal className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{dashboardStats?.total_signals || 0}</div>
              <p className="text-xs text-slate-400">
                نجح منها {dashboardStats?.successful_signals || 0} إشارة
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">معدل النجاح</CardTitle>
              <Target className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {dashboardStats?.success_rate ? `${dashboardStats.success_rate.toFixed(1)}%` : '0%'}
              </div>
              <Progress 
                value={dashboardStats?.success_rate || 0} 
                className="mt-2"
              />
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">المحافظ النشطة</CardTitle>
              <Wallet className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{dashboardStats?.total_wallets || 0}</div>
              <p className="text-xs text-slate-400">
                محفظة مراقبة
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">الإشارات المعلقة</CardTitle>
              <Clock className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{dashboardStats?.pending_signals || 0}</div>
              <p className="text-xs text-slate-400">
                في انتظار التقييم
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="signals" className="space-y-6">
          <TabsList className="bg-slate-800/50 border-slate-700">
            <TabsTrigger value="signals" className="data-[state=active]:bg-blue-600">
              الإشارات الحديثة
            </TabsTrigger>
            <TabsTrigger value="wallets" className="data-[state=active]:bg-purple-600">
              أفضل المحافظ
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-green-600">
              التحليلات
            </TabsTrigger>
          </TabsList>

          <TabsContent value="signals" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Signal className="h-5 w-5 mr-2 text-blue-400" />
                  الإشارات الحديثة
                </CardTitle>
                <CardDescription className="text-slate-400">
                  آخر {recentSignals.length} إشارة تم تحليلها
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentSignals.map((signal, index) => (
                    <div key={signal.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                      <div className="flex items-center space-x-4 rtl:space-x-reverse">
                        {getStatusIcon(signal.performance_status)}
                        <div>
                          <p className="font-medium text-white">
                            {signal.token_name || 'غير محدد'}
                          </p>
                          <p className="text-sm text-slate-400">
                            {signal.contract_address?.slice(0, 8)}...{signal.contract_address?.slice(-8)}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        {getDecisionBadge(signal.decision)}
                        <p className="text-sm text-slate-400 mt-1">
                          {signal.total_wallets_involved} محفظة
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="wallets" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Users className="h-5 w-5 mr-2 text-purple-400" />
                  أفضل المحافظ أداءً
                </CardTitle>
                <CardDescription className="text-slate-400">
                  المحافظ ذات أعلى معدل نجاح
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topWallets.map((wallet, index) => (
                    <div key={wallet.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                      <div className="flex items-center space-x-4 rtl:space-x-reverse">
                        <div className="bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-white">
                            {wallet.wallet_type} #{wallet.wallet_number}
                          </p>
                          <p className="text-sm text-slate-400">
                            {wallet.total_calls} استدعاء إجمالي
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-2 rtl:space-x-reverse">
                          <TrendingUp className="h-4 w-4 text-green-400" />
                          <span className="text-green-400 font-bold">
                            {(wallet.success_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-sm text-slate-400">
                          {wallet.successful_calls} نجح
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2 text-green-400" />
                    إحصائيات الأداء
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">الإشارات الناجحة</span>
                      <span className="text-green-400 font-bold">
                        {dashboardStats?.successful_signals || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">الإشارات الفاشلة</span>
                      <span className="text-red-400 font-bold">
                        {(dashboardStats?.total_signals || 0) - (dashboardStats?.successful_signals || 0) - (dashboardStats?.pending_signals || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">الإشارات المعلقة</span>
                      <span className="text-yellow-400 font-bold">
                        {dashboardStats?.pending_signals || 0}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <DollarSign className="h-5 w-5 mr-2 text-yellow-400" />
                    معلومات النظام
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">حالة النظام</span>
                      <Badge className="bg-green-600 text-white">نشط</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">آخر تحديث</span>
                      <span className="text-slate-400 text-sm">
                        {new Date().toLocaleString('ar-SA')}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">الإصدار</span>
                      <span className="text-blue-400">v1.0.0</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App

