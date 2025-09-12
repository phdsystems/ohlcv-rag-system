#!/usr/bin/env python3
"""
OOP-based Main Entry Point for OHLCV RAG System
"""

import os
import sys
import argparse
from typing import Optional, List
from dotenv import load_dotenv

from src.application import OHLCVRAGApplication

load_dotenv()


class CLI:
    """Command Line Interface for OHLCV RAG Application"""
    
    def __init__(self):
        self.app: Optional[OHLCVRAGApplication] = None
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="OHLCV RAG System - Financial Data Analysis with RAG",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Setup command
        setup_parser = subparsers.add_parser('setup', help='Setup the system with initial data')
        setup_parser.add_argument('--tickers', nargs='+', 
                                 default=['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
                                 help='Ticker symbols to ingest')
        setup_parser.add_argument('--source', default='yahoo',
                                 choices=['yahoo', 'alpha_vantage', 'polygon', 'csv'],
                                 help='Data source')
        setup_parser.add_argument('--period', default='1y',
                                 help='Data period (e.g., 1y, 6mo, 3mo)')
        setup_parser.add_argument('--interval', default='1d',
                                 help='Data interval (e.g., 1d, 1h, 5m)')
        
        # Query command
        query_parser = subparsers.add_parser('query', help='Query the RAG system')
        query_parser.add_argument('question', help='Your question about the data')
        query_parser.add_argument('--type', default='general',
                                 choices=['general', 'pattern', 'comparison', 'prediction', 'technical'],
                                 help='Query type')
        query_parser.add_argument('--n-results', type=int, default=5,
                                 help='Number of results to retrieve')
        
        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', help='Perform specific analysis')
        analyze_parser.add_argument('analysis_type',
                                   choices=['pattern', 'trend', 'comparison', 'indicator'],
                                   help='Type of analysis')
        analyze_parser.add_argument('--tickers', nargs='+',
                                   help='Tickers to analyze')
        analyze_parser.add_argument('--pattern', help='Pattern type for pattern analysis')
        analyze_parser.add_argument('--indicator', help='Indicator for indicator analysis')
        
        # Interactive command
        subparsers.add_parser('interactive', help='Enter interactive mode')
        
        # Status command
        subparsers.add_parser('status', help='Show system status')
        
        # Clear command
        subparsers.add_parser('clear', help='Clear all data')
        
        return parser
    
    def run(self, args: argparse.Namespace) -> None:
        """Run the CLI with given arguments"""
        
        # Initialize application
        if args.command != 'status' or not self.app:
            self._initialize_app()
        
        # Execute command
        if args.command == 'setup':
            self._setup(args)
        elif args.command == 'query':
            self._query(args)
        elif args.command == 'analyze':
            self._analyze(args)
        elif args.command == 'interactive':
            self._interactive()
        elif args.command == 'status':
            self._status()
        elif args.command == 'clear':
            self._clear()
        else:
            self.parser.print_help()
    
    def _initialize_app(self) -> None:
        """Initialize the application"""
        print("Initializing OHLCV RAG Application...")
        
        try:
            self.app = OHLCVRAGApplication()
            self.app.initialize()
            print("✓ Application initialized successfully\n")
        except Exception as e:
            print(f"✗ Failed to initialize application: {e}")
            sys.exit(1)
    
    def _setup(self, args: argparse.Namespace) -> None:
        """Setup the system with initial data"""
        print("=" * 60)
        print("OHLCV RAG System Setup")
        print("=" * 60)
        
        print(f"\nConfiguration:")
        print(f"- Data Source: {args.source}")
        print(f"- Tickers: {', '.join(args.tickers)}")
        print(f"- Period: {args.period}")
        print(f"- Interval: {args.interval}")
        
        # Update application config if needed
        self.app.config['ingestion'].update({
            'source': args.source,
            'period': args.period,
            'interval': args.interval
        })
        
        # Reinitialize ingestion with new config
        self.app.data_ingestion.config.update(self.app.config['ingestion'])
        
        print("\nIngesting data...")
        result = self.app.ingest_data(args.tickers)
        
        if result['success']:
            print(f"\n✓ Data ingestion complete!")
            print(f"  - Chunks created: {result['chunks_created']}")
            print(f"  - Documents indexed: {result['documents_indexed']}")
        else:
            print(f"\n✗ Data ingestion failed: {result.get('error', 'Unknown error')}")
    
    def _query(self, args: argparse.Namespace) -> None:
        """Process a query"""
        print(f"\nProcessing query: {args.question}")
        print("-" * 40)
        
        context = {'n_results': args.n_results}
        result = self.app.query(args.question, args.type, context)
        
        if result.get('success') is False:
            print(f"✗ Query failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"\nAnswer:\n{result['answer']}")
            print(f"\nSources used: {len(result.get('sources', []))}")
            print(f"Confidence: {result.get('confidence', 0):.2%}")
            print(f"Processing time: {result.get('processing_time', 0):.2f}s")
    
    def _analyze(self, args: argparse.Namespace) -> None:
        """Perform analysis"""
        print(f"\nPerforming {args.analysis_type} analysis...")
        print("-" * 40)
        
        parameters = {}
        if args.pattern:
            parameters['pattern_type'] = args.pattern
        if args.indicator:
            parameters['indicator'] = args.indicator
        
        result = self.app.analyze(args.analysis_type, args.tickers, parameters)
        
        if result.get('success') is False:
            print(f"✗ Analysis failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"\nAnalysis Type: {result.get('analysis_type')}")
            print(f"Findings:")
            for key, value in result.get('findings', {}).items():
                print(f"  - {key}: {value}")
            
            if result.get('recommendations'):
                print(f"\nRecommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
            
            if result.get('risk_factors'):
                print(f"\nRisk Factors:")
                for risk in result['risk_factors']:
                    print(f"  - {risk}")
    
    def _interactive(self) -> None:
        """Enter interactive mode"""
        print("\n" + "=" * 60)
        print("Interactive Query Mode")
        print("=" * 60)
        
        interactive = InteractiveMode(self.app)
        interactive.run()
    
    def _status(self) -> None:
        """Show system status"""
        print("\n" + "=" * 60)
        print("System Status")
        print("=" * 60)
        
        status = self.app.get_status()
        
        print(f"\nApplication Status: {status['state']['status']}")
        print(f"Initialized: {status['initialized']}")
        
        print(f"\nComponents:")
        for component, comp_status in status['components'].items():
            if comp_status:
                print(f"  - {component}: {comp_status.get('name', 'Unknown')} "
                      f"[{'✓' if comp_status.get('initialized') else '✗'}]")
        
        print(f"\nStatistics:")
        stats = status['state']['statistics']
        print(f"  - Total Queries: {stats['total_queries']}")
        print(f"  - Successful Queries: {stats['successful_queries']}")
        print(f"  - Success Rate: {stats['success_rate']:.1f}%")
        print(f"  - Uptime: {stats['uptime_seconds']:.0f} seconds")
        
        print(f"\nIngested Tickers: {', '.join(status['state']['ingested_tickers']) or 'None'}")
    
    def _clear(self) -> None:
        """Clear all data"""
        print("\nAre you sure you want to clear all data? (y/n): ", end="")
        if input().strip().lower() == 'y':
            if self.app.clear_data():
                print("✓ All data cleared successfully")
            else:
                print("✗ Failed to clear data")
        else:
            print("Operation cancelled")


class InteractiveMode:
    """Interactive mode for the application"""
    
    def __init__(self, app: OHLCVRAGApplication):
        self.app = app
    
    def run(self) -> None:
        """Run interactive mode"""
        print("\nCommands:")
        print("  query <question> - Ask any question about the data")
        print("  pattern <type> [ticker] - Analyze patterns")
        print("  indicator <name> <condition> <value> - Search by indicator")
        print("  status - Show system status")
        print("  help - Show this help message")
        print("  exit - Exit interactive mode")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'exit':
                    print("Exiting interactive mode...")
                    break
                
                elif command == 'help':
                    self.run()  # Show help again
                
                elif command == 'status':
                    self._show_status()
                
                elif command == 'query':
                    if args:
                        self._process_query(args)
                    else:
                        print("Please provide a question")
                
                elif command == 'pattern':
                    self._analyze_pattern(args)
                
                elif command == 'indicator':
                    self._analyze_indicator(args)
                
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_status(self) -> None:
        """Show brief status"""
        status = self.app.get_status()
        state = status['state']
        print(f"Status: {state['status']}")
        print(f"Ingested tickers: {', '.join(state['ingested_tickers']) or 'None'}")
        print(f"Total queries: {state['statistics']['total_queries']}")
    
    def _process_query(self, question: str) -> None:
        """Process a query"""
        print("Processing...")
        result = self.app.query(question)
        
        if result.get('success') is False:
            print(f"Error: {result.get('error')}")
        else:
            print(f"\n{result['answer']}")
            print(f"\n[Sources: {len(result.get('sources', []))}, "
                  f"Confidence: {result.get('confidence', 0):.2%}]")
    
    def _analyze_pattern(self, args: str) -> None:
        """Analyze pattern"""
        parts = args.split()
        if not parts:
            print("Please specify pattern type (uptrend, downtrend, breakout, etc.)")
            return
        
        pattern_type = parts[0]
        tickers = parts[1:] if len(parts) > 1 else None
        
        print(f"Analyzing {pattern_type} pattern...")
        result = self.app.analyze('pattern', tickers, {'pattern_type': pattern_type})
        
        if result.get('success') is False:
            print(f"Error: {result.get('error')}")
        else:
            for key, value in result.get('findings', {}).items():
                print(f"  {key}: {value}")
    
    def _analyze_indicator(self, args: str) -> None:
        """Analyze indicator"""
        parts = args.split()
        if len(parts) < 3:
            print("Format: indicator <name> <condition> <value>")
            print("Example: indicator RSI > 70")
            return
        
        indicator = parts[0]
        condition = parts[1]
        try:
            threshold = float(parts[2])
        except ValueError:
            print("Invalid threshold value")
            return
        
        print(f"Analyzing {indicator} {condition} {threshold}...")
        result = self.app.analyze('indicator', None, {
            'indicators': [indicator],
            'condition': condition,
            'threshold': threshold
        })
        
        if result.get('success') is False:
            print(f"Error: {result.get('error')}")
        else:
            for key, value in result.get('findings', {}).items():
                print(f"  {key}: {value}")


def main():
    """Main entry point"""
    cli = CLI()
    args = cli.parser.parse_args()
    
    try:
        cli.run(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()