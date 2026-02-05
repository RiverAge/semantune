import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronDown, ChevronRight, Star, Database, Settings } from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: any;
  badge?: number;
  badgeColor?: 'green' | 'yellow' | 'red';
}

interface NavGroup {
  title: string;
  icon: any;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: '核心功能',
    icon: Star,
    items: [
      { path: '/recommend', label: '智能推荐', icon: () => <span className="text-xl">🎯</span> },
      { path: '/query', label: '歌曲查询', icon: () => <span className="text-xl">🔍</span> },
      { path: '/analyze', label: '用户分析', icon: () => <span className="text-xl">👥</span> },
    ],
  },
  {
    title: '数据管理',
    icon: Database,
    items: [
      { path: '/tagging', label: '标签生成', icon: () => <span className="text-xl">🏷️</span> },
      { path: '/duplicate', label: '重复检测', icon: () => <span className="text-xl">⚠️</span> },
    ],
  },
  {
    title: '系统',
    icon: Settings,
    items: [
      { path: '/logs', label: '日志', icon: () => <span className="text-xl">📋</span> },
      { path: '/settings', label: '配置', icon: () => <span className="text-xl">⚙️</span> },
    ],
  },
];

export default function Navigation() {
  const location = useLocation();
  const navRef = useRef<HTMLDivElement>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [closingGroups, setClosingGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (groupTitle: string) => {
    const newExpanded = new Set(expandedGroups);
    const newClosing = new Set(closingGroups);

    if (newExpanded.has(groupTitle)) {
      newExpanded.delete(groupTitle);
      newClosing.add(groupTitle);
      setExpandedGroups(newExpanded);
      setClosingGroups(newClosing);
      setTimeout(() => {
        setClosingGroups(prev => {
          const updated = new Set(prev);
          updated.delete(groupTitle);
          return updated;
        });
      }, 200);
    } else {
      newExpanded.clear();
      newExpanded.add(groupTitle);
      setExpandedGroups(newExpanded);
    }
  };

  const closeAllGroups = () => {
    if (expandedGroups.size === 0) return;
    const newClosing = new Set([...expandedGroups]);
    setExpandedGroups(new Set());
    setClosingGroups(newClosing);
    setTimeout(() => {
      setClosingGroups(new Set());
    }, 200);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(event.target as Node)) {
        closeAllGroups();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [expandedGroups]);

  const getBadgeColor = (color?: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-100 text-green-700';
      case 'yellow':
        return 'bg-yellow-100 text-yellow-700';
      case 'red':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 py-2">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-xl">🎵</span>
            <span className="text-lg font-bold text-gray-900">Navidrome+</span>
          </div>

          {/* 导航分组 */}
          <div className="flex flex-wrap items-center gap-1" ref={navRef}>
            {navGroups.map((group) => {
              const GroupIcon = group.icon;
              const isExpanded = expandedGroups.has(group.title);
              const isGroupActive = group.items.some(item => location.pathname === item.path);

              return (
                <div key={group.title} className="relative">
                  {/* 组标题 */}
                  <button
                    onClick={() => toggleGroup(group.title)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isGroupActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <GroupIcon className="h-4 w-4" />
                    <span>{group.title}</span>
                    {isExpanded || closingGroups.has(group.title) ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                  </button>

                  {/* 下拉菜单 */}
                  {(isExpanded || closingGroups.has(group.title)) && (
                    <div
                      className={`absolute left-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 origin-top overflow-hidden ${
                        isExpanded
                          ? 'opacity-100 scale-y-100'
                          : 'opacity-0 scale-y-95 pointer-events-none'
                      } transition-all duration-200 ease-out`}
                    >
                      {group.items.map((item) => {
                        const isActive = location.pathname === item.path;
                        const ItemIcon = item.icon;

                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => closeAllGroups()}
                            className={`flex items-center justify-between px-4 py-2 text-sm transition-colors ${
                              isActive
                                ? 'bg-primary-50 text-primary-700'
                                : 'text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <ItemIcon />
                              <span>{item.label}</span>
                              {item.badge !== undefined && item.badge > 0 && (
                                <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(item.badgeColor)}`}>
                                  {item.badge}
                                </span>
                              )}
                            </div>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            {/* 首页按钮 */}
            <Link
              to="/"
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/'
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <span>🏠</span>
              首页
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
