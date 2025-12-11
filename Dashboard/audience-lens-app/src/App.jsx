import { useState, useMemo } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

// Моковые данные на основе ваших JSON файлов
const MOCK_AUDIENCE_DATA = {
  "product": {
    "product_id": "wb_drill",
    "name": "Дрель-шуруповерт аккумуляторный 2 в 1 с насадками и 2 АКБ"
  },
  "models": {
    "qwen/qwen3-32b": {
      "parsed": {
        "product_id": "396501168",
        "product_name": "Дрель-шуруповерт аккумуляторный 2 в 1 с насадками и 2 АКБ",
        "summary": "Бюджетный универсальный инструмент с комплектом аккумуляторов и насадок, ориентированный на домашних мастеров и профессионалов, требующих надежности и функциональности.",
        "audience_segments": [
          {
            "name": "Домашние мастера",
            "share_pct_est": 45,
            "needs": "Универсальность, простота использования, наличие комплекта для базовых задач",
            "pain_points": "Ограничения в мощности, недостаток долговечности для частого использования",
            "recommended_message": "Все в одном: дрель и шуруповерт с 24 насадками для ремонта дома и дачи!"
          },
          {
            "name": "Профессиональные строители",
            "share_pct_est": 30,
            "needs": "Высокая мощность, ударный режим, быстрая зарядка и долговечность",
            "pain_points": "Недостаточная емкость аккумуляторов, отсутствие дополнительных функций",
            "recommended_message": "Профессиональная надежность: 59 Н·м крутящего момента и 2 аккумулятора для непрерывной работы!"
          },
          {
            "name": "Молодые семьи/студенты",
            "share_pct_est": 25,
            "needs": "Бюджетная стоимость, компактность, минимальная сложность в освоении",
            "pain_points": "Ограниченная долговечность, отсутствие расширенной гарантии",
            "recommended_message": "Первый инструмент для дома: 1298 руб. с чемоданом и 24 насадками!"
          }
        ],
        "recommendations": [
          "Акцентировать в описании совместимость с популярными битами DeWalt для профессионалов",
          "Добавить информацию о времени работы от аккумулятора и скорости зарядки",
          "Создать комплектующие (например, дополнительные биты) как отдельный товар с скидкой"
        ],
        "a_b_test_hypotheses": [
          "Тестирование двух вариантов заголовка: 'Для дома и стройки' vs 'Профессиональный инструмент'",
          "Сравнение эффективности изображений с акцентом на мощность vs комплектацию",
          "Тестирование ценовой стратегии: '1298 руб. с 2 АКБ' vs '1298 руб. (экономия 500 руб. на аккумуляторах)'"
        ]
      }
    }
  }
};

const MOCK_REVIEWS_DATA = [
  {
    "review_id": "wb_pos_1",
    "product_id": "wb_drill",
    "model": "qwen/qwen3-32b",
    "result": {
      "тональность": "положительный",
      "критерии": [
        {"критерий": "Информативность", "оценка": 3, "обоснование": "Отзыв содержит конкретный пример использования (сборка стеллажа) и описание проблемы с битами"},
        {"критерий": "Релевантность", "оценка": 4, "обоснование": "Отзыв фокусируется на ключевых характеристиках продукта"},
        {"критерий": "Опыт использования", "оценка": 4, "обоснование": "Автор делится личным опытом и эмоциями"},
        {"критерий": "Ответы на вопросы", "оценка": 4, "обоснование": "Отзыв отвечает на вопросы о качестве бит и общем впечатлении"},
        {"критерий": "Контекст", "оценка": 2, "обоснование": "Отсутствует информация о климатических условиях"},
        {"критерий": "Сравнение", "оценка": 1, "обоснование": "Нет сравнения с аналогами"},
        {"критерий": "Нарушение правил", "оценка": 5, "обоснование": "Отзыв соответствует правилам платформы"},
        {"критерий": "Конфликт интересов", "оценка": 5, "обоснование": "Нет признаков аффилированности"}
      ]
    }
  },
  {
    "review_id": "wb_neu_1",
    "product_id": "wb_drill",
    "model": "qwen/qwen3-32b",
    "result": {
      "тональность": "нейтральный",
      "критерии": [
        {"критерий": "Информативность", "оценка": 2, "обоснование": "Отзыв содержит минимальные сведения"},
        {"критерий": "Релевантность", "оценка": 3, "обоснование": "Упоминается соответствие цены и базовой функциональности"},
        {"критерий": "Опыт использования", "оценка": 2, "обоснование": "Отсутствуют субъективные ощущения"},
        {"критерий": "Ответы на вопросы", "оценка": 2, "обоснование": "Не раскрываются критичные для покупателя аспекты"},
        {"критерий": "Контекст", "оценка": 1, "обоснование": "Не указаны условия эксплуатации"},
        {"критерий": "Сравнение", "оценка": 1, "обоснование": "Отсутствуют сравнения с аналогами"},
        {"критерий": "Нарушение правил", "оценка": 5, "обоснование": "Отзыв соответствует правилам платформы"},
        {"критерий": "Конфликт интересов", "оценка": 5, "обоснование": "Не выявлены признаки аффилированности"}
      ]
    }
  },
  {
    "review_id": "wb_neg_1",
    "product_id": "wb_drill",
    "model": "qwen/qwen3-32b",
    "result": {
      "тональность": "отрицательный",
      "критерии": [
        {"критерий": "Информативность", "оценка": 4, "обоснование": "Отзыв содержит конкретные факты: сломалась рукоятка молотка"},
        {"критерий": "Релевантность", "оценка": 2, "обоснование": "Отзыв частично соответствует заявленным функциям"},
        {"критерий": "Опыт использования", "оценка": 5, "обоснование": "Автор делится личным опытом, описывает эмоции"},
        {"критерий": "Ответы на вопросы", "оценка": 3, "обоснование": "Отзыв отвечает на вопросы о недостатках и качестве"},
        {"критерий": "Контекст", "оценка": 2, "обоснование": "Указан сценарий использования (сборка столика)"},
        {"критерий": "Сравнение", "оценка": 1, "обоснование": "Отзыв не содержит сравнений с аналогами"},
        {"критерий": "Нарушение правил", "оценка": 5, "обоснование": "Отзыв не содержит признаков фейковости"},
        {"критерий": "Конфликт интересов", "оценка": 5, "обоснование": "Нет указаний на связь автора с конкурентами"}
      ]
    }
  }
];

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

  // Извлекаем данные
  const audienceData = MOCK_AUDIENCE_DATA.models['qwen/qwen3-32b'].parsed;
  const segments = audienceData.audience_segments;

  // Анализ тональности отзывов
  const sentimentData = useMemo(() => {
    const counts = { 'положительный': 0, 'нейтральный': 0, 'отрицательный': 0 };
    MOCK_REVIEWS_DATA.forEach(review => {
      const sentiment = review.result.тональность;
      counts[sentiment]++;
    });
    return [
      { name: 'Положительные', value: counts['положительный'], color: COLORS.positive },
      { name: 'Нейтральные', value: counts['нейтральный'], color: COLORS.neutral },
      { name: 'Отрицательные', value: counts['отрицательный'], color: COLORS.danger }
    ];
  }, []);

  // Средние оценки по критериям
  const criteriaAverages = useMemo(() => {
    const criteriaSums = {};
    const criteriaCounts = {};

    MOCK_REVIEWS_DATA.forEach(review => {
      review.result.критерии.forEach(crit => {
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
      средняя: (criteriaSums[name] / criteriaCounts[name]).toFixed(1)
    }));
  }, []);

  // Данные для радар-чарта
  const radarData = criteriaAverages.map(item => ({
    subject: item.критерий.length > 15 ? item.критерий.substring(0, 15) + '...' : item.критерий,
    value: parseFloat(item.средняя),
    fullMax: 5
  }));

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
          <div>
            <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: '700', color: COLORS.primary }}>
              Audience Lens
            </h1>
            <p style={{ margin: '0.25rem 0 0 0', color: COLORS.neutral, fontSize: '0.95rem' }}>
              Анализ отзывов и сегментация аудитории
            </p>
          </div>
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

      {/* Content */}
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
                  fill="#8884d8"
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

          {/* Качество отзывов */}
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
        </div>
      )}

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
                borderLeft: `6px solid ${COLORS.chartColors[index % COLORS.chartColors.length]}`,
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                <div>
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
                    fontWeight: '600'
                  }}>
                    {segment.share_pct_est}% аудитории
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: '1rem', marginTop: '1.5rem' }}>
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.neutral, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    💡 Потребности
                  </h4>
                  <p style={{ margin: 0, color: COLORS.primary, lineHeight: '1.6' }}>
                    {segment.needs}
                  </p>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.neutral, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ⚠️ Болевые точки
                  </h4>
                  <p style={{ margin: 0, color: COLORS.primary, lineHeight: '1.6' }}>
                    {segment.pain_points}
                  </p>
                </div>

                <div style={{
                  background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
                  padding: '1rem',
                  borderRadius: '0.75rem',
                  marginTop: '0.5rem'
                }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', color: COLORS.primary, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
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

      {activeTab === 'reviews' && (
        <div>
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

          <div style={{ display: 'grid', gap: '1.5rem' }}>
            {MOCK_REVIEWS_DATA.map((review) => {
              const sentimentColor = 
                review.result.тональность === 'положительный' ? COLORS.positive :
                review.result.тональность === 'отрицательный' ? COLORS.danger :
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
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
                      {review.result.тональность}
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: '1rem',
                    marginTop: '1rem'
                  }}>
                    {review.result.критерии.map((crit, critIndex) => (
                      <div
                        key={critIndex}
                        style={{
                          background: '#f8fafc',
                          padding: '1rem',
                          borderRadius: '0.5rem'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
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
                          {crit.обоснование.substring(0, 100)}...
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
              {audienceData.a_b_test_hypotheses.map((hyp, index) => (
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
        </div>
      )}
    </div>
  );
}

export default App;