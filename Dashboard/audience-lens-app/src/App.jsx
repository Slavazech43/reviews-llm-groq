import { useState, useMemo, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const COLORS = {
  primary: '#0f172a',
  secondary: '#1e293b',
  accent: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  neutral: '#64748b',
  background: '#f8fafc',
  cardBg: '#ffffff',
  positive: '#10b981',
  negative: '#ef4444',
  chartColors: ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
};

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rawData, setRawData] = useState({
    audience: null,
    product: null,
    reviews: null,
    results: null
  });

  // Загрузка всех файлов
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 Загрузка файлов...');

      const [audienceRes, productRes, reviewsRes, resultsRes] = await Promise.all([
        fetch('/audience_analysis_results.json'),
        fetch('/product.json'),
        fetch('/reviews.json'),
        fetch('/results.json')
      ]);

      const audience = audienceRes.ok ? await audienceRes.json() : null;
      const product = productRes.ok ? await productRes.json() : null;
      const reviews = reviewsRes.ok ? await reviewsRes.json() : null;
      const results = resultsRes.ok ? await resultsRes.json() : null;

      console.log('📊 Загруженные данные:', { audience, product, reviews, results });

      if (!audience) {
        throw new Error('Не найден файл audience_analysis_results.json');
      }

      setRawData({ audience, product, reviews, results });
      setLoading(false);

    } catch (err) {
      console.error('❌ Ошибка загрузки:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  // Обработка данных из audience_analysis_results.json
  const audienceData = useMemo(() => {
    if (!rawData.audience) return null;

    // Структура: массив[0].models['qwen/qwen3-32b'].parsed
    const data = rawData.audience[0];
    const parsed = data.models['qwen/qwen3-32b'].parsed;

    return {
      product_name: parsed.product_name,
      summary: parsed.summary,
      segments: parsed.audience_segments,
      recommendations: parsed.recommendations,
      ab_tests: parsed.a_b_test_hypotheses
    };
  }, [rawData.audience]);

  // Обработка results.json для отзывов с оценками
  const reviewsData = useMemo(() => {
    if (!rawData.results) return [];

    return rawData.results.map(result => {
      // Определяем тональность
      let sentiment = 'нейтральный';
      if (result.result?.тональность) {
        sentiment = result.result.тональность;
      } else if (result.overall_sentiment) {
        sentiment = result.overall_sentiment === 'positive' ? 'положительный' :
                   result.overall_sentiment === 'negative' ? 'отрицательный' : 'нейтральный';
      }

      // Извлекаем критерии
      let criteria = [];
      if (result.result?.критерии) {
        criteria = result.result.критерии;
      } else if (result.criteria_scores) {
        criteria = Object.entries(result.criteria_scores).map(([key, value]) => ({
          критерий: key,
          оценка: value,
          обоснование: result.key_points?.[0] || 'Анализ качества'
        }));
      }

      return {
        review_id: result.review_id || result.id,
        product_id: result.product_id,
        text: result.review_text || '',
        sentiment: sentiment,
        criteria: criteria
      };
    });
  }, [rawData.results]);

  // Анализ тональности
  const sentimentData = useMemo(() => {
    if (!reviewsData.length) return [];

    const counts = { 'положительный': 0, 'нейтральный': 0, 'отрицательный': 0 };
    reviewsData.forEach(review => {
      counts[review.sentiment]++;
    });

    return [
      { name: 'Положительные', value: counts['положительный'], color: COLORS.positive },
      { name: 'Нейтральные', value: counts['нейтральный'], color: COLORS.neutral },
      { name: 'Отрицательные', value: counts['отрицательный'], color: COLORS.danger }
    ];
  }, [reviewsData]);

  // Средние оценки по критериям
  const criteriaAverages = useMemo(() => {
    if (!reviewsData.length) return [];

    const criteriaSums = {};
    const criteriaCounts = {};

    reviewsData.forEach(review => {
      review.criteria.forEach(crit => {
        const name = crit.критерий;
        if (!criteriaSums[name]) {
          criteriaSums[name] = 0;
          criteriaCounts[name] = 0;
        }
        criteriaSums[name] += crit.оценка;
        criteriaCounts[name]++;
      });
    });

    return Object.keys(criteriaSums).map(name => ({
      критерий: name,
      средняя: parseFloat((criteriaSums[name] / criteriaCounts[name]).toFixed(1))
    }));
  }, [reviewsData]);

  // Данные для радар-чарта
  const radarData = useMemo(() => {
    return criteriaAverages.map(item => ({
      subject: item.критерий.length > 15 ? item.критерий.substring(0, 15) + '...' : item.критерий,
      value: item.средняя,
      fullMax: 5
    }));
  }, [criteriaAverages]);

  // Экраны загрузки и ошибок
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: '1.5rem',
        fontFamily: "'Inter', sans-serif"
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⏳</div>
          <div>Загрузка данных...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Inter', sans-serif",
        padding: '2rem'
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '1rem',
          padding: '3rem',
          maxWidth: '600px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>❌</div>
          <h2 style={{ color: COLORS.danger, marginBottom: '1rem' }}>Ошибка загрузки</h2>
          <p style={{ color: COLORS.neutral, marginBottom: '2rem' }}>{error}</p>
          <button
            onClick={loadAllData}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '0.75rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            🔄 Попробовать снова
          </button>
          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            background: '#fef3c7',
            borderRadius: '0.5rem',
            textAlign: 'left'
          }}>
            <strong style={{ color: '#92400e' }}>Проверьте:</strong>
            <ul style={{ color: '#92400e', marginTop: '0.5rem', marginLeft: '1rem' }}>
              <li>Файлы в папке public/</li>
              <li>Запущен python audience_analysis_groq.py</li>
              <li>Запущен python reviews_groq_criteria.py</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (!audienceData) {
    return <div>Нет данных</div>;
  }

  const segments = audienceData.segments;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      padding: '2rem'
    }}>
      {/* Header */}
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: '1rem',
        padding: '2rem',
        marginBottom: '2rem',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{
            width: '60px',
            height: '60px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem'
          }}>
            📊
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: '700', color: COLORS.primary }}>
              Audience Lens
            </h1>
            <p style={{ margin: '0.25rem 0 0 0', color: COLORS.neutral, fontSize: '0.95rem' }}>
              Анализ отзывов и сегментация аудитории
            </p>
          </div>
          <button
            onClick={loadAllData}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '0.75rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s ease'
            }}
          >
            🔄 Обновить
          </button>
        </div>
        
        <div style={{
          background: '#f1f5f9',
          padding: '1rem',
          borderRadius: '0.75rem',
          marginTop: '1rem'
        }}>
          <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: '600', color: COLORS.primary }}>
            {audienceData.product_name}
          </h2>
          <p style={{ margin: 0, color: COLORS.neutral, lineHeight: '1.6' }}>
            {audienceData.summary}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '2rem',
        flexWrap: 'wrap'
      }}>
        {[
          { id: 'overview', label: '📈 Обзор' },
          { id: 'segments', label: '👥 Сегменты' },
          { id: 'reviews', label: '💬 Отзывы' },
          { id: 'recommendations', label: '💡 Рекомендации' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.75rem 1.5rem',
              background: activeTab === tab.id 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                : 'rgba(255, 255, 255, 0.95)',
              color: activeTab === tab.id ? 'white' : COLORS.primary,
              border: 'none',
              borderRadius: '0.75rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: activeTab === tab.id 
                ? '0 10px 30px rgba(102, 126, 234, 0.4)' 
                : '0 4px 12px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              transform: activeTab === tab.id ? 'translateY(-2px)' : 'none'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content - Overview */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
          {/* Сегменты аудитории */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: '1rem',
            padding: '2rem',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.3rem', fontWeight: '700', color: COLORS.primary }}>
              Сегменты аудитории
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={segments}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, share_pct_est }) => `${name}: ${share_pct_est}%`}
                  outerRadius={100}
                  dataKey="share_pct_est"
                >
                  {segments.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS.chartColors[index % COLORS.chartColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Тональность отзывов */}
          {sentimentData.length > 0 && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '1rem',
              padding: '2rem',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
            }}>
              <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.3rem', fontWeight: '700', color: COLORS.primary }}>
                Тональность отзывов
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sentimentData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fill: COLORS.neutral }} />
                  <YAxis tick={{ fill: COLORS.neutral }} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Качество отзывов */}
          {radarData.length > 0 && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '1rem',
              padding: '2rem',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
              gridColumn: 'span 2'
            }}>
              <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.3rem', fontWeight: '700', color: COLORS.primary }}>
                Качество отзывов по критериям
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: COLORS.neutral, fontSize: 12 }} />
                  <PolarRadiusAxis domain={[0, 5]} tick={{ fill: COLORS.neutral }} />
                  <Radar name="Средняя оценка" dataKey="value" stroke="#667eea" fill="#667eea" fillOpacity={0.6} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Content - Segments */}
      {activeTab === 'segments' && (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {segments.map((segment, index) => (
            <div
              key={index}
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '1rem',
                padding: '2rem',
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
                borderLeft: `6px solid ${COLORS.chartColors[index % COLORS.chartColors.length]}`
              }}
            >
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', fontWeight: '700', color: COLORS.primary }}>
                {segment.name}
              </h3>
              <div style={{
                display: 'inline-block',
                background: COLORS.chartColors[index % COLORS.chartColors.length],
                color: 'white',
                padding: '0.25rem 0.75rem',
                borderRadius: '1rem',
                fontSize: '0.9rem',
                fontWeight: '600',
                marginBottom: '1rem'
              }}>
                {segment.share_pct_est}% аудитории
              </div>

              <div style={{ display: 'grid', gap: '1rem' }}>
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.neutral, fontSize: '0.9rem', textTransform: 'uppercase' }}>
                    💡 Потребности
                  </h4>
                  <p style={{ margin: 0, color: COLORS.primary, lineHeight: '1.6' }}>
                    {segment.needs}
                  </p>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.neutral, fontSize: '0.9rem', textTransform: 'uppercase' }}>
                    ⚠️ Болевые точки
                  </h4>
                  <p style={{ margin: 0, color: COLORS.primary, lineHeight: '1.6' }}>
                    {segment.pain_points}
                  </p>
                </div>

                <div style={{
                  background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
                  padding: '1rem',
                  borderRadius: '0.75rem'
                }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.primary, fontSize: '0.9rem', textTransform: 'uppercase' }}>
                    📣 Рекомендуемое сообщение
                  </h4>
                  <p style={{ margin: 0, color: COLORS.primary, fontSize: '1.05rem', fontWeight: '600', lineHeight: '1.6' }}>
                    "{segment.recommended_message}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Content - Reviews */}
      {activeTab === 'reviews' && (
        <div>
          {criteriaAverages.length > 0 && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '1rem',
              padding: '2rem',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
              marginBottom: '2rem'
            }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.3rem', fontWeight: '700', color: COLORS.primary }}>
                Средние оценки по критериям
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={criteriaAverages} layout="vertical" margin={{ left: 150 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" domain={[0, 5]} tick={{ fill: COLORS.neutral }} />
                  <YAxis dataKey="критерий" type="category" tick={{ fill: COLORS.neutral, fontSize: 12 }} width={140} />
                  <Tooltip />
                  <Bar dataKey="средняя" fill="#667eea" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div style={{ display: 'grid', gap: '1.5rem' }}>
            {reviewsData.map((review) => {
              const sentimentColor = 
                review.sentiment === 'положительный' ? COLORS.positive :
                review.sentiment === 'отрицательный' ? COLORS.danger :
                COLORS.neutral;

              return (
                <div
                  key={review.review_id}
                  style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: '1rem',
                    padding: '2rem',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
                    borderLeft: `6px solid ${sentimentColor}`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: COLORS.primary }}>
                      Отзыв #{review.review_id}
                    </h4>
                    <div style={{
                      background: sentimentColor,
                      color: 'white',
                      padding: '0.35rem 1rem',
                      borderRadius: '1rem',
                      fontSize: '0.9rem',
                      fontWeight: '600'
                    }}>
                      {review.sentiment}
                    </div>
                  </div>

                  {review.text && (
                    <p style={{ 
                      margin: '0 0 1rem 0', 
                      color: COLORS.neutral, 
                      lineHeight: '1.6',
                      fontStyle: 'italic',
                      padding: '1rem',
                      background: '#f8fafc',
                      borderRadius: '0.5rem'
                    }}>
                      {review.text}
                    </p>
                  )}

                  {review.criteria.length > 0 && (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                      gap: '1rem'
                    }}>
                      {review.criteria.map((crit, critIndex) => (
                        <div key={critIndex} style={{ background: '#f8fafc', padding: '1rem', borderRadius: '0.5rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.85rem', color: COLORS.neutral, fontWeight: '600' }}>
                              {crit.критерий}
                            </span>
                            <span style={{
                              background: crit.оценка >= 4 ? COLORS.positive : crit.оценка >= 3 ? COLORS.warning : COLORS.danger,
                              color: 'white',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '0.5rem',
                              fontSize: '0.85rem',
                              fontWeight: '700'
                            }}>
                              {crit.оценка}/5
                            </span>
                          </div>
                          <p style={{ margin: 0, fontSize: '0.8rem', color: COLORS.neutral, lineHeight: '1.4' }}>
                            {crit.обоснование.substring(0, 100)}{crit.обоснование.length > 100 ? '...' : ''}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Content - Recommendations */}
      {activeTab === 'recommendations' && (
        <div style={{ display: 'grid', gap: '2rem' }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: '1rem',
            padding: '2rem',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
          }}>
            <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem', fontWeight: '700', color: COLORS.primary }}>
              💡 Рекомендации по улучшению
            </h3>
            <div style={{ display: 'grid', gap: '1rem' }}>
              {audienceData.recommendations.map((rec, index) => (
                <div
                  key={index}
                  style={{
                    background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
                    padding: '1.5rem',
                    borderRadius: '0.75rem',
                    borderLeft: '4px solid #667eea'
                  }}
                >
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'start' }}>
                    <div style={{
                      background: '#667eea',
                      color: 'white',
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      flexShrink: 0
                    }}>
                      {index + 1}
                    </div>
                    <p style={{ margin: 0, color: COLORS.primary, fontSize: '1.05rem', lineHeight: '1.6' }}>
                      {rec}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {audienceData.ab_tests && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: '1rem',
              padding: '2rem',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)'
            }}>
              <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem', fontWeight: '700', color: COLORS.primary }}>
                🧪 Гипотезы для A/B тестирования
              </h3>
              <div style={{ display: 'grid', gap: '1rem' }}>
                {audienceData.ab_tests.map((hyp, index) => (
                  <div
                    key={index}
                    style={{
                      background: 'linear-gradient(135deg, #764ba215 0%, #667eea15 100%)',
                      padding: '1.5rem',
                      borderRadius: '0.75rem',
                      borderLeft: '4px solid #764ba2'
                    }}
                  >
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'start' }}>
                      <div style={{
                        background: '#764ba2',
                        color: 'white',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '0.5rem',
                        fontWeight: '700',
                        fontSize: '0.85rem',
                        flexShrink: 0
                      }}>
                        A/B #{index + 1}
                      </div>
                      <p style={{ margin: 0, color: COLORS.primary, fontSize: '1.05rem', lineHeight: '1.6' }}>
                        {hyp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;